from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient
from core.models import Recipe, Tag, Ingredient
from ..serializers import RecipeSerializer, RecipeDetailSerializer

RECIPE_URL = reverse('recipe:recipe-list')


def detail_recipe(recipe_id):
    """Return Recipe detail url"""

    return reverse('recipe:recipe-detail', args=[recipe_id])


def sample_tag(user, name='Main course'):
    """Create sample tags"""

    return Tag.objects.create(user=user, name=name)


def sample_ingredient(user, name='Cinnamon'):
    """Create sample ingredients"""

    return Ingredient.objects.create(user=user, name=name)


def sample_recipe(user, **params):
    """Create sample recipe"""

    defaults = {
        'title': 'sample recipe',
        'time_minutes': 10,
        'price': 34.00
    }

    defaults.update(params)
    return Recipe.objects.create(user=user, **defaults)


class PublicRecipeApiTests(TestCase):
    """Test unauthenticated recipe Api access """

    def setUp(self):
        self.client = APIClient()

    def test_required_auth(self):
        """Test the authenticated is required"""

        res = self.client.get(RECIPE_URL)

        self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)


class PrivateRecipeApiTests(TestCase):
    """Test authenticated recipe access"""

    def setUp(self):
        self.client = APIClient()
        self.user = get_user_model().objects.create_user('test@email.com', 'testpass')
        self.client.force_authenticate(user=self.user)

    def test_retrieve_recipe(self):
        """Test retrieving list of recipe"""

        sample_recipe(user=self.user)
        sample_recipe(user=self.user)
        res = self.client.get(RECIPE_URL)
        recipes = Recipe.objects.all()

        serializer = RecipeSerializer(recipes, many=True)
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data, serializer.data)

    def test_recipes_limited_to_user(self):
        """"Test retrieving recipes for user"""
        user2 = get_user_model().objects.create_user(
            'other@email.com',
            'password123'
        )
        sample_recipe(user=user2)
        sample_recipe(user=self.user)

        res = self.client.get(RECIPE_URL)

        recipes = Recipe.objects.filter(user=self.user)
        serializer = RecipeSerializer(recipes, many=True)
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(len(res.data), 1)
        self.assertEqual(res.data, serializer.data)

    def test_view_recipe_detail(self):
        """Test a viewing recipe detail"""

        recipe = sample_recipe(user=self.user)
        recipe.tags.add(sample_tag(user=self.user))
        recipe.ingredients.add(sample_ingredient(user=self.user))
        url = detail_recipe(recipe.id)
        res = self.client.get(url)

        serializer = RecipeDetailSerializer(recipe)

        self.assertEqual(res.data, serializer.data)

    def test_create_basic_recipe(self):
        """Create a new recipe"""

        payload = {
            'title': 'Chocolate cheesecake',
            'time_minutes': 4,
            'price': 33.00
        }

        res = self.client.post(RECIPE_URL, payload)

        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        recipe = Recipe.objects.get(id=res.data['id'])
        for key in payload.keys():
            self.assertEqual(payload[key], getattr(recipe, key))

    def test_create_recipe_with_tags(self):
        """Test a creating recipe with tag"""

        tag1 = sample_tag(user=self.user, name='Vegan')
        tag2 = sample_tag(user=self.user, name='Dessert')
        payload = {
            'title': 'Avocado lime cheesecake',
            'tags': [tag1.id, tag2.id],
            'time_minutes': 3,
            'price': 34.00
        }

        res = self.client.post(RECIPE_URL, payload)

        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        recipe = Recipe.objects.get(id=res.data['id'])
        tags = recipe.tags.all()
        self.assertEqual(tags.count(), 2)
        self.assertIn(tag1, tags)
        self.assertIn(tag2, tags)

    def test_create_recipe_with_ingredients(self):
        """Test a creating recipe with ingredients"""

        ingredient1 = sample_ingredient(user=self.user, name='Prawns')
        ingredient2 = sample_ingredient(user=self.user, name='Ginger')
        payload = {
            'title': 'Thai prawn red curry',
            'ingredients': [ingredient1.id, ingredient2.id],
            'time_minutes': 34,
            'price': 344.00
        }

        res = self.client.post(RECIPE_URL, payload)

        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        recipe = Recipe.objects.get(id=res.data['id'])
        ingredients = recipe.ingredients.all()
        self.assertEqual(ingredients.count(), 2)
        self.assertIn(ingredient1, ingredients)
        self.assertIn(ingredient2, ingredients)
