import os
from rest_framework import viewsets, status, filters
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.db.models import Q
from django.http import FileResponse
from django_filters.rest_framework import DjangoFilterBackend
from .models import Folder, Tag, Document, DocumentVersion, DocumentActivity, Comment
from .serializers import (
    FolderSerializer,
    FolderDetailSerializer,
    TagSerializer,
    DocumentSerializer,
    DocumentDetailSerializer,
    DocumentVersionSerializer,
    DocumentActivitySerializer,
    CommentSerializer,
)
from .permissions import IsOwnerOrAdmin, IsOwnerAdminOrShared


class TagViewSet(viewsets.ModelViewSet):
    """
    ViewSet for viewing and editing tags
    """
    queryset = Tag.objects.all()
    serializer_class = TagSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['name']
    ordering_fields = ['name']

    def get_permissions(self):
        if self.action in ['create', 'update', 'partial_update', 'destroy']:
            self.permission_classes = [IsAuthenticated]
        return super().get_permissions()


class FolderViewSet(viewsets.ModelViewSet):
    """
    ViewSet for viewing and editing folders
    """
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['is_public', 'parent']
    search_fields = ['name', 'description']
    ordering_fields = ['name', 'created_at', 'modified_at']
    permission_classes = [IsAuthenticated, IsOwnerAdminOrShared]

    def get_queryset(self):
        user = self.request.user
        # Include folders owned by user, shared with user, or public
        return Folder.objects.filter(
            Q(owner=user) |
            Q(shared_users=user) |
            Q(is_public=True)
        ).distinct()

    def get_serializer_class(self):
        if self.action in ['retrieve', 'update', 'partial_update']:
            return FolderDetailSerializer
        return FolderSerializer

    def perform_create(self, serializer):
        serializer.save(owner=self.request.user)

    @action(detail=True)
    def contents(self, request, pk=None):
        """
        Get contents of a folder (subfolders and documents)
        """
        folder = self.get_object()
        subfolders = Folder.objects.filter(parent=folder)
        documents = Document.objects.filter(folder=folder)

        subfolder_serializer = FolderSerializer(subfolders, many=True, context={'request': request})
        document_serializer = DocumentSerializer(documents, many=True, context={'request': request})

        return Response({
            'subfolders': subfolder_serializer.data,
            'documents': document_serializer.data
        })

    @action(detail=True, methods=['post'])
    def share(self, request, pk=None):
        """
        Share folder with users
        """
        folder = self.get_object()
        user_ids = request.data.get('user_ids', [])

        if user_ids:
            folder.shared_users.add(*user_ids)

        serializer = self.get_serializer(folder)
        return Response(serializer.data)

    @action(detail=True, methods=['post'])
    def unshare(self, request, pk=None):
        """
        Unshare folder from users
        """
        folder = self.get_object()
        user_ids = request.data.get('user_ids', [])

        if user_ids:
            folder.shared_users.remove(*user_ids)

        serializer = self.get_serializer(folder)
        return Response(serializer.data)


class DocumentViewSet(viewsets.ModelViewSet):
    """
    ViewSet for viewing and editing documents
    """
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['is_public', 'folder', 'tags']
    search_fields = ['title', 'description', 'file_type']
    ordering_fields = ['title', 'created_at', 'modified_at', 'file_size']
    permission_classes = [IsAuthenticated, IsOwnerAdminOrShared]

    def get_queryset(self):
        user = self.request.user
        # Include documents owned by user, shared with user, or public
        return Document.objects.filter(
            Q(owner=user) |
            Q(shared_users=user) |
            Q(is_public=True)
        ).distinct()

    def get_serializer_class(self):
        if self.action in ['retrieve', 'update', 'partial_update']:
            return DocumentDetailSerializer
        return DocumentSerializer

    def perform_create(self, serializer):
        serializer.save(owner=self.request.user)

    def perform_destroy(self, instance):
        # Log activity before deletion
        DocumentActivity.objects.create(
            document=None,
            user=self.request.user,
            activity_type='deleted',
            description=f'Deleted document: {instance.title}',
            ip_address=self.request.META.get('REMOTE_ADDR')
        )
        instance.delete()

    @action(detail=True, methods=['get'])
    def download(self, request, pk=None):
        """
        Download document file
        """
        document = self.get_object()

        # Log access activity
        DocumentActivity.objects.create(
            document=document,
            user=request.user,
            activity_type='accessed',
            description='Downloaded document',
            ip_address=request.META.get('REMOTE_ADDR')
        )

        file_path = document.file.path
        return FileResponse(
            open(file_path, 'rb'),
            as_attachment=True,
            filename=os.path.basename(document.file.name)
        )

    @action(detail=True, methods=['get'])
    def versions(self, request, pk=None):
        """
        Get all versions of a document
        """
        document = self.get_object()
        versions = document.versions.all()
        serializer = DocumentVersionSerializer(versions, many=True, context={'request': request})
        return Response(serializer.data)

    @action(detail=True, methods=['post'])
    def share(self, request, pk=None):
        """
        Share document with users
        """
        document = self.get_object()
        user_ids = request.data.get('user_ids', [])

        if user_ids:
            document.shared_users.add(*user_ids)

        # Log sharing activity
        DocumentActivity.objects.create(
            document=document,
            user=request.user,
            activity_type='shared',
            description=f'Shared with {len(user_ids)} users',
            ip_address=request.META.get('REMOTE_ADDR')
        )

        serializer = self.get_serializer(document)
        return Response(serializer.data)

    @action(detail=True, methods=['post'])
    def unshare(self, request, pk=None):
        """
        Unshare document from users
        """
        document = self.get_object()
        user_ids = request.data.get('user_ids', [])

        if user_ids:
            document.shared_users.remove(*user_ids)

        # Log unsharing activity
        DocumentActivity.objects.create(
            document=document,
            user=request.user,
            activity_type='unshared',
            description=f'Unshared from {len(user_ids)} users',
            ip_address=request.META.get('REMOTE_ADDR')
        )

        serializer = self.get_serializer(document)
        return Response(serializer.data)

    @action(detail=True, methods=['get', 'post'])
    def comments(self, request, pk=None):
        """
        Get or add comments to a document
        """
        document = self.get_object()

        if request.method == 'GET':
            comments = document.comments.all()
            serializer = CommentSerializer(comments, many=True, context={'request': request})
            return Response(serializer.data)

        # POST method - add comment
        serializer = CommentSerializer(data=request.data, context={'request': request})
        serializer.is_valid(raise_exception=True)
        serializer.save(document=document, user=request.user)

        # Log comment activity
        DocumentActivity.objects.create(
            document=document,
            user=request.user,
            activity_type='commented',
            description='Added a comment',
            ip_address=request.META.get('REMOTE_ADDR')
        )

        return Response(serializer.data, status=status.HTTP_201_CREATED)


class DocumentVersionViewSet(viewsets.ReadOnlyModelViewSet):
    """
    ViewSet for viewing document versions (read-only)
    """
    serializer_class = DocumentVersionSerializer
    permission_classes = [IsAuthenticated, IsOwnerAdminOrShared]

    def get_queryset(self):
        user = self.request.user
        # Only include versions of documents the user has access to
        return DocumentVersion.objects.filter(
            Q(document__owner=user) |
            Q(document__shared_users=user) |
            Q(document__is_public=True)
        ).distinct()

    @action(detail=True, methods=['get'])
    def download(self, request, pk=None):
        """
        Download a specific version of a document
        """
        version = self.get_object()
        document = version.document

        # Log access activity
        DocumentActivity.objects.create(
            document=document,
            user=request.user,
            activity_type='accessed',
            description=f'Downloaded document version {version.version}',
            ip_address=request.META.get('REMOTE_ADDR')
        )

        file_path = version.file.path
        return FileResponse(
            open(file_path, 'rb'),
            as_attachment=True,
            filename=f"{os.path.splitext(os.path.basename(version.file.name))[0]}_v{version.version}{os.path.splitext(version.file.name)[1]}"
        )


class CommentViewSet(viewsets.ModelViewSet):
    """
    ViewSet for viewing and editing comments
    """
    serializer_class = CommentSerializer
    permission_classes = [IsAuthenticated, IsOwnerOrAdmin]

    def get_queryset(self):
        user = self.request.user
        # Only include comments on documents the user has access to
        return Comment.objects.filter(
            Q(document__owner=user) |
            Q(document__shared_users=user) |
            Q(document__is_public=True)
        ).distinct()

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)


class DocumentActivityViewSet(viewsets.ReadOnlyModelViewSet):
    """
    ViewSet for viewing document activities (read-only)
    """
    serializer_class = DocumentActivitySerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_fields = ['activity_type', 'document']
    ordering_fields = ['created_at']

    def get_queryset(self):
        user = self.request.user
        # Only show activities for documents the user is the owner of
        if user.is_staff or hasattr(user, 'is_admin') and user.is_admin:
            return DocumentActivity.objects.all()
        return DocumentActivity.objects.filter(document__owner=user)