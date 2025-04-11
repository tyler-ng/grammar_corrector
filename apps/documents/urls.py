from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    FolderViewSet,
    TagViewSet,
    DocumentViewSet,
    DocumentVersionViewSet,
    CommentViewSet,
    DocumentActivityViewSet,
)

router = DefaultRouter()
router.register('folders', FolderViewSet, basename='folder')
router.register('tags', TagViewSet, basename='tag')
router.register('versions', DocumentVersionViewSet, basename='documentversion')
router.register('comments', CommentViewSet, basename='comment')
router.register('activities', DocumentActivityViewSet, basename='documentactivity')
router.register('', DocumentViewSet, basename='document')

urlpatterns = [
    path('', include(router.urls)),
]