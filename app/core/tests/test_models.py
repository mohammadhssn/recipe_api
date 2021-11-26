from django.test import TestCase
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from ..models import Tag, Ingredient


def sample_user(email='test@email.com', password='testpass'):
    """Create a sample user"""
    return get_user_model().objects.create_user(email, password)


class ModelTests(TestCase):

    def test_create_user_with_email_success(self):
        """Test creating a new user with an email successfully"""
        email = 'test@email.com'
        password = 'testpassword'
        user = get_user_model().objects.create_user(
            email=email,
            password=password
        )

        self.assertEqual(user.email, email)
        self.assertTrue(user.check_password(password))

    def test_new_user_email_normalized(self):
        """Test th email for a new user is normalized"""
        email = 'test@EMAIL.COM'
        user = get_user_model().objects.create_user(email=email, password='pass123')

        self.assertEqual(user.email, email.lower())

    def test_new_user_invalid_email(self):
        """Test creating user with no email raises error"""
        with self.assertRaises(ValidationError):
            get_user_model().objects.create_user(None, 'pass123')

    def test_create_new_superuser(self):
        """Test creating a new superuser"""
        user = get_user_model().objects.create_superuser(
            'test@email.com',
            'pass123'
        )

        self.assertTrue(user.is_staff)
        self.assertTrue(user.is_superuser)

    # Tag
    def test_tag_str(self):
        """Test the tag string representation"""

        tag = Tag.objects.create(user=sample_user(), name='vegan')

        self.assertEqual(str(tag), tag.name)

    # ingredient
    def test_ingredient_str(self):
        """Test the ingredient string representation"""

        ingredient = Ingredient.objects.create(user=sample_user(), name='tomato')

        self.assertEqual(str(ingredient), ingredient.name)
