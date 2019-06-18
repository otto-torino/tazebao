from django.conf import settings

from rest_framework_httpsignature.authentication import SignatureAuthentication
from rest_framework import exceptions

from .models import Client


class NewsletterAPISignatureAuthentication(SignatureAuthentication):
    # The HTTP header used to pass the consumer key ID.
    # Defaults to 'X-Api-Key'.
    API_KEY_HEADER = 'X-Api-Key'

    # A method to fetch (User instance, user_secret_string) from the
    # consumer key ID, or None in case it is not found.
    def fetch_user_data(self, api_key):
        try:
            client = Client.objects.get(id_key=api_key)
            return (client.user, client.secret_key)
        except Client.DoesNotExist:
            return None


class PostfixNewsletterAPISignatureAuthentication(SignatureAuthentication):
    # The HTTP header used to pass the consumer key ID.
    # Defaults to 'X-Api-Key'.
    API_KEY_HEADER = 'X-Api-Key'

    # A method which returns True or False if this is a postfix request
    def authenticate(self, request):
        # Check for API key header.
        api_key_header = self.header_canonical(self.API_KEY_HEADER)
        api_key = request.META.get(api_key_header)
        if not api_key:
            raise exceptions.AuthenticationFailed('Missing API key')

        # Check if request has a "Signature" request header.
        authorization_header = self.header_canonical('Authorization')
        sent_string = request.META.get(authorization_header)
        if not sent_string:
            raise exceptions.AuthenticationFailed('No signature provided')
        sent_signature = self.get_signature_from_signature_string(sent_string)

        # Fetch credentials for API key from the data store.
        if not api_key == settings.POSTFIX_CLIENT_ID:
            raise exceptions.AuthenticationFailed('Bad API key')

        # Build string to sign from "headers" part of Signature value.
        computed_string = self.build_signature(api_key, settings.POSTFIX_CLIENT_SECRET, request)
        computed_signature = self.get_signature_from_signature_string(
            computed_string)

        if computed_signature != sent_signature:
            raise exceptions.AuthenticationFailed('Bad signature')

        return True
