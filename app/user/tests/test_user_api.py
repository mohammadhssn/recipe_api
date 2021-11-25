from django.test import TestCase
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient
from rest_framework import status
from django.urls import reverse

CREATE_USER_URL = reverse('user:create')
CREATE_TOKEN_URL = reverse('user:token')
ME_URL = reverse('user:me')


def create_user(**params):
    return get_user_model().objects.create_user(**params)


class PublicUserApiTests(TestCase):
    """Test the users Api (public)"""

    def setUp(self):
        self.client = APIClient()

    def test_create_valid_user_success(self):
        """Test creating user with valid payload is successful"""

        payload = {
            'email': 'test@email.com',
            'password': 'testpass',
            'name': 'test name'
        }

        res = self.client.post(CREATE_USER_URL, payload)
        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        user = get_user_model().objects.get(**res.data)
        self.assertTrue(user.check_password(payload.get('password')))
        self.assertNotIn('password', res.data)

    def test_user_exists(self):
        """Test creating user that already exists fails"""

        payload = {
            'email': 'test@email.com',
            'password': 'testpass'
        }
        create_user(**payload)

        res = self.client.post(CREATE_USER_URL, payload)
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)

    def test_password_to_short(self):
        """Test that the password must be more than 5 character"""

        payload = {
            'email': 'test@email.com',
            'password': 'pw'
        }

        res = self.client.post(CREATE_USER_URL, payload)
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)
        user_exist = get_user_model().objects.filter(
            email=payload.get('email')
        ).exists()
        self.assertFalse(user_exist)

    # Token
    def test_create_token_for_user(self):
        """Test that a token is created for the user"""

        payload = {'email': 'test@email.com', 'password': 'testpass'}
        create_user(**payload)
        res = self.client.post(CREATE_TOKEN_URL, payload)

        self.assertIn('token', res.data)
        self.assertEqual(res.status_code, status.HTTP_200_OK)

    def test_create_token_invalid_credential(self):
        """Test that token is not created if invalid credential are given"""

        create_user(email='test@email.com', password='testpass')
        payload = {'email': 'test@email.com', 'password': 'wrong'}
        res = self.client.post(CREATE_TOKEN_URL, payload)

        self.assertNotIn('token', res.data)
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)

    def test_create_token_not_user(self):
        """Test that token is not created if user doens't exists"""

        payload = {'email': 'test@email.com', 'password': 'testpass'}
        res = self.client.post(CREATE_TOKEN_URL, payload)

        self.assertNotIn('token', res.data)
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)

    def test_create_token_missing_field(self):
        """Test that email and password are required"""

        payload = {'email': 'test', 'password': ''}
        res = self.client.post(CREATE_TOKEN_URL, payload)

        self.assertNotIn('token', res.data)
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)

    # ME
    def test_retrieve_user_unauthoruzed(self):
        """Test that authentication is required of user"""

        res = self.client.get(ME_URL)

        self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)


class PrivateUserApiTests(TestCase):
    """Test api request that require authentication"""

    def setUp(self):
        self.user = create_user(email='test@email.com', password='testpass', name='test')
        self.client = APIClient()
        self.client.force_authenticate(user=self.user)

    def test_retrieve_profile_success(self):
        """Test retrieving profile for legged in user"""

        res = self.client.get(ME_URL)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertTrue(res.data, {'email': self.user.email, 'name': self.user.name})

    def test_post_me_not_allowed(self):
        """Test that post in not allowed on the me url"""

        res = self.client.post(ME_URL, {})

        self.assertEqual(res.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)

    def test_update_user_profile(self):
        """Test updating the user profile for authenticated user"""

        payload = {'name': 'new_name', 'password': 'newpass123'}
        res = self.client.patch(ME_URL, payload)
        self.user.refresh_from_db()

        self.assertEqual(self.user.name, payload.get('name'))
        self.assertTrue(self.user.check_password(payload.get('password')))
        self.assertEqual(res.status_code, status.HTTP_200_OK)
