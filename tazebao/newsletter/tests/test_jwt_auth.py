import json

from .base import PASSWORD, NewsletterTestCase

LOGIN_URL = '/api/v1/login/'
REFRESH_URL = '/api/v1/refresh-token/'
WHOAMI_URL = '/api/v1/whoami/'


class JwtAuthTest(NewsletterTestCase):
    """Contract used by the React web app and the desktop app."""

    def login(self, password=PASSWORD):
        return self.client.post(
            LOGIN_URL, data=json.dumps({'username': 'client1', 'password': password}),
            content_type='application/json')

    def test_login_returns_token(self):
        response = self.login()
        self.assertEqual(response.status_code, 200)
        self.assertEqual(list(response.json().keys()), ['token'])

    def test_login_wrong_password(self):
        response = self.login('wrong')
        self.assertEqual(response.status_code, 400)
        self.assertNotIn('token', response.json())

    def test_whoami_with_jwt_header(self):
        token = self.login().json()['token']
        response = self.client.get(WHOAMI_URL, HTTP_AUTHORIZATION='JWT %s' % token)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), {
            'userId': self.user.id,
            'userName': 'client1',
            'userEmail': 'client1@example.com',
            'isSuperUser': False,
            'client': {'idKey': 'key00001', 'secretKey': 's' * 32, 'suggestionsPerDay': 3},
        })

    def test_whoami_anonymous(self):
        response = self.client.get(WHOAMI_URL)
        self.assertEqual(response.status_code, 401)

    def test_invalid_token(self):
        response = self.client.get('/api/v1/newsletter/subscriberlist/', HTTP_AUTHORIZATION='JWT not-a-token')
        self.assertEqual(response.status_code, 401)

    def test_refresh_returns_new_usable_token(self):
        token = self.login().json()['token']
        response = self.client.post(
            REFRESH_URL, data=json.dumps({'token': token}), content_type='application/json')
        self.assertEqual(response.status_code, 200)
        new_token = response.json()['token']
        response = self.client.get(WHOAMI_URL, HTTP_AUTHORIZATION='JWT %s' % new_token)
        self.assertEqual(response.status_code, 200)

    def test_api_with_jwt(self):
        token = self.login().json()['token']
        response = self.client.get('/api/v1/newsletter/subscriberlist/', HTTP_AUTHORIZATION='JWT %s' % token)
        self.assertEqual(response.status_code, 200)
        self.assertEqual([item['name'] for item in response.json()], ['Main'])

    def test_mosaico_app_with_bearer_querystring(self):
        """The React app embeds the mosaico editor in an iframe passing ?bearer=<token>."""
        token = self.login().json()['token']
        response = self.client.get('/mosaico/app.html?bearer=%s' % token)
        self.assertEqual(response.status_code, 200)

    def test_mosaico_app_without_bearer(self):
        response = self.client.get('/mosaico/app.html')
        self.assertIn(response.status_code, (401, 403))
