from rest_framework_httpsignature.authentication import SignatureAuthentication

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
