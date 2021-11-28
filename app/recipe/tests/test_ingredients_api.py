from rest_framework import status
from django.test import TestCase
from django.urls import reverse
from django.contrib.auth import get_user_model
from core.models import Ingredient, Recipe
from ..serializers import IngredientSerializer
from rest_framework.test import APIClient

INGREDIENT_URL = reverse('recipe:ingredient-list')


class PublicIngredientApiTests(TestCase):
    """Test the publicly available ingredient api"""

    def setUp(self):
        self.client = APIClient()

    def test_login_required(self):
        """Test than login required for retrieving ingredient"""

        res = self.client.get(INGREDIENT_URL)

        self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)


class PrivateIngredientApiTests(TestCase):
    """Test ingredient can be retrieved by authorized user"""

    def setUp(self):
        self.client = APIClient()
        self.user = get_user_model().objects.create_user(email='test@email.com', password='testpass')
        self.client.force_authenticate(self.user)

    def test_retrieve_ingredient_list(self):
        """Test retrieving a list og ingredients"""

        Ingredient.objects.create(user=self.user, name='kale')
        Ingredient.objects.create(user=self.user, name='salt')

        res = self.client.get(INGREDIENT_URL)
        ingredients = Ingredient.objects.all().order_by('-name')
        serializer = IngredientSerializer(ingredients, many=True)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data, serializer.data)

    def test_ingredient_limited_to_user(self):
        """Test that only ingredients for authenticated user are returned"""

        user2 = get_user_model().objects.create_user(email='user2@email.com', password='pass123')
        Ingredient.objects.create(user=user2, name='Vinegar')
        ingredient = Ingredient.objects.create(user=self.user, name='Tumeric')

        res = self.client.get(INGREDIENT_URL)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(len(res.data), 1)
        self.assertEqual(res.data[0]['name'], ingredient.name)

    def test_create_ingredient_successful(self):
        """Test Creating a new user"""

        payload = {'name': 'Cabbage'}
        res = self.client.post(INGREDIENT_URL, payload)
        ingredient_exists = Ingredient.objects.filter(user=self.user, name=payload.get('name')).exists()

        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        self.assertTrue(ingredient_exists)

    def test_create_ingredient_invalid(self):
        """Test creating a new ingredient with invalid payload"""

        payload = {'name': ''}
        res = self.client.post(INGREDIENT_URL, payload)

        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)

    # filter
    def test_retrieve_ingredients_assigned_to_recipe(self):
        """Test filtering ingredients by those assigned recipes"""

        ingredient1 = Ingredient.objects.create(user=self.user, name='Turkey')
        ingredient2 = Ingredient.objects.create(user=self.user, name='Apple')
        recipe1 = Recipe.objects.create(
            title='Porridge',
            time_minutes=3,
            price=2.00,
            user=self.user
        )
        recipe1.ingredients.add(ingredient1)

        res = self.client.get(INGREDIENT_URL, {'assigned_only': 1})
        serializer1 = IngredientSerializer(ingredient1)
        serializer2 = IngredientSerializer(ingredient2)

        self.assertIn(serializer1.data, res.data)
        self.assertNotIn(serializer2.data, res.data)

    def test_retrieve_ingredients_assigned_unique(self):
        """Test filtering tags by assigned returns unique items"""

        ingredient1 = Ingredient.objects.create(user=self.user, name='Turkey')
        Ingredient.objects.create(user=self.user, name='Apple')
        recipe1 = Recipe.objects.create(
            title='Porridge',
            time_minutes=3,
            price=2.00,
            user=self.user
        )
        recipe1.ingredients.add(ingredient1)
        recipe2 = Recipe.objects.create(
            title='Coriander eggs on toast',
            time_minutes=4,
            price=99,
            user=self.user
        )
        recipe2.ingredients.add(ingredient1)

        res = self.client.get(INGREDIENT_URL, {'assigned_only': 1})

        self.assertEqual(len(res.data), 1)
