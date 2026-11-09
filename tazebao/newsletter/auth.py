"""HMAC request signature authentication.

Implements the subset of draft-cavage-http-signatures used by Tazebao
clients and by the Postfix bounce script, byte-compatible with the
previously used djangorestframework-httpsignature + httpsig libraries
(both unmaintained):

    Authorization: Signature keyId="<ID_KEY>",algorithm="hmac-sha256",headers="date",signature="<SIG>"
    X-Api-Key: <ID_KEY>

    SIG = Base64(HMAC-SHA256(SECRET_KEY, "date: <Date header>"))

The server always verifies with hmac-sha256, whatever "algorithm" says.
"""
import base64
import hashlib
import hmac
import re

from django.conf import settings
from rest_framework import authentication, exceptions

from .models import Client


class SignatureAuthentication(authentication.BaseAuthentication):
    SIGNATURE_RE = re.compile('signature="(.+?)"')
    SIGNATURE_HEADERS_RE = re.compile(r'headers="([\(\)\sa-z0-9-]+?)"')

    API_KEY_HEADER = 'X-Api-Key'

    def get_signature_from_signature_string(self, signature):
        """Return the signature from the signature header or None."""
        match = self.SIGNATURE_RE.search(signature or '')
        if not match:
            return None
        return match.group(1)

    def get_headers_from_signature(self, signature):
        """Header names covered by the signature, "date" when not specified."""
        match = self.SIGNATURE_HEADERS_RE.search(signature or '')
        if not match:
            return ['date']
        return match.group(1).split()

    def header_canonical(self, header_name):
        """Translate HTTP headers to Django request.META names."""
        header_name = header_name.lower()
        if header_name == 'content-type':
            return 'CONTENT-TYPE'
        elif header_name == 'content-length':
            return 'CONTENT-LENGTH'
        return 'HTTP_%s' % header_name.replace('-', '_').upper()

    def build_message(self, request, signature_headers):
        lines = []
        for header in signature_headers:
            header = header.lower()
            if header == '(request-target)':
                lines.append('%s: %s %s' % (header, request.method.lower(), request.get_full_path()))
            else:
                # a missing header was signed as "None" by httpsig: kept as is
                lines.append('%s: %s' % (header, request.META.get(self.header_canonical(header))))
        return '\n'.join(lines).encode('ascii')

    def compute_signature(self, secret, request):
        sent_string = request.META.get(self.header_canonical('Authorization'))
        message = self.build_message(request, self.get_headers_from_signature(sent_string))
        digest = hmac.new(secret.encode('ascii'), message, hashlib.sha256).digest()
        return base64.b64encode(digest).decode('ascii')

    def verify(self, secret, sent_signature, request):
        if not secret or not sent_signature:
            return False
        try:
            computed = self.compute_signature(secret, request)
        except UnicodeEncodeError:
            return False
        return hmac.compare_digest(computed, sent_signature)

    def get_credentials(self, request):
        """Return (api_key, sent_signature), or None when no API key was sent."""
        api_key = request.META.get(self.header_canonical(self.API_KEY_HEADER))
        if not api_key:
            return None
        sent_string = request.META.get(self.header_canonical('Authorization'))
        if not sent_string:
            raise exceptions.AuthenticationFailed('No signature provided')
        return api_key, self.get_signature_from_signature_string(sent_string)

    def fetch_user_data(self, api_key):
        """Return (User instance, API secret) or None if api_key is bad."""
        return None

    def authenticate(self, request):
        credentials = self.get_credentials(request)
        if credentials is None:
            return None
        api_key, sent_signature = credentials

        user_data = self.fetch_user_data(api_key)
        if not user_data:
            raise exceptions.AuthenticationFailed('Bad API key')
        user, secret = user_data

        if not self.verify(secret, sent_signature, request):
            raise exceptions.AuthenticationFailed('Bad signature')

        return (user, api_key)


class NewsletterAPISignatureAuthentication(SignatureAuthentication):
    """API clients: credentials are the Client id_key / secret_key."""

    def fetch_user_data(self, api_key):
        try:
            client = Client.objects.get(id_key=api_key)
            return (client.user, client.secret_key)
        except Client.DoesNotExist:
            return None


class PostfixNewsletterAPISignatureAuthentication(SignatureAuthentication):
    """The mail server posting bounces: credentials come from settings.

    Used by hand in FailedEmailApiView, returns True or raises AuthenticationFailed.
    """

    def authenticate(self, request):
        credentials = self.get_credentials(request)
        if credentials is None:
            raise exceptions.AuthenticationFailed('Missing API key')
        api_key, sent_signature = credentials

        if not settings.POSTFIX_CLIENT_ID or api_key != settings.POSTFIX_CLIENT_ID:
            raise exceptions.AuthenticationFailed('Bad API key')

        if not self.verify(settings.POSTFIX_CLIENT_SECRET, sent_signature, request):
            raise exceptions.AuthenticationFailed('Bad signature')

        return True
