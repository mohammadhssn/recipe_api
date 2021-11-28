from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework import viewsets, mixins, status
from rest_framework.authentication import TokenAuthentication
from rest_framework.permissions import IsAuthenticated
from .serializers import TagSerializer, IngredientSerializer, RecipeSerializer, RecipeDetailSerializer, \
    RecipeImageSerializer
from core.models import Tag, Ingredient, Recipe


class BaseViewSetAttr(viewsets.GenericViewSet, mixins.ListModelMixin, mixins.CreateModelMixin):
    """Base ViewSet for user owned recipe attributes"""

    authentication_classes = (TokenAuthentication,)
    permission_classes = (IsAuthenticated,)

    def get_queryset(self):
        """Return object for the current authentication user only"""

        return self.queryset.filter(user=self.request.user).order_by('-name')

    def perform_create(self, serializer):
        """Create a new tag"""

        serializer.save(user=self.request.user)


class TagViewSet(BaseViewSetAttr):
    """Manage tags in the database"""

    serializer_class = TagSerializer
    queryset = Tag.objects.all()


class IngredientViewSet(BaseViewSetAttr):
    """Manage ingredient in the database"""

    serializer_class = IngredientSerializer
    queryset = Ingredient.objects.all()


class RecipeViewSet(viewsets.ModelViewSet):
    """Mange recipe in the database"""

    authentication_classes = (TokenAuthentication,)
    permission_classes = (IsAuthenticated,)
    queryset = Recipe.objects.all()
    serializer_class = RecipeSerializer

    def get_queryset(self):
        """Return object for the current authentication user only"""

        return self.queryset.filter(user=self.request.user)

    def get_serializer_class(self):
        """return appropriate serialize class"""
        if self.action == 'retrieve':
            return RecipeDetailSerializer
        elif self.action == 'upload_image':
            return RecipeImageSerializer

        return self.serializer_class

    def perform_create(self, serializer):
        """Create a new recipe"""

        serializer.save(user=self.request.user)

    @action(methods=['POST'], detail=True, url_path='upload-image')
    def upload_image(self, request, pk=None):
        recipe = self.get_object()
        serializer = self.get_serializer(
            recipe,
            data=request.data
        )
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
