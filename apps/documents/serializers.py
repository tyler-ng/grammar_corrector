from rest_framework import serializers
from .models import Folder, Tag, Document, DocumentVersion, DocumentActivity, Comment
from django.contrib.auth import get_user_model

User = get_user_model()


class UserMinimalSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'first_name', 'last_name']


class TagSerializer(serializers.ModelSerializer):
    class Meta:
        model = Tag
        fields = ['id', 'name', 'slug']
        read_only_fields = ['slug']


class FolderSerializer(serializers.ModelSerializer):
    owner = UserMinimalSerializer(read_only=True)
    parent_id = serializers.PrimaryKeyRelatedField(
        source='parent', queryset=Folder.objects.all(),
        required=False, allow_null=True, write_only=True
    )

    class Meta:
        model = Folder
        fields = ['id', 'name', 'description', 'parent', 'parent_id', 'owner',
                  'created_at', 'modified_at', 'is_public']
        read_only_fields = ['created_at', 'modified_at']

    def create(self, validated_data):
        validated_data['owner'] = self.context['request'].user
        return super().create(validated_data)


class FolderDetailSerializer(FolderSerializer):
    shared_users = UserMinimalSerializer(many=True, read_only=True)
    shared_users_ids = serializers.PrimaryKeyRelatedField(
        source='shared_users', queryset=User.objects.all(),
        many=True, required=False, write_only=True
    )

    class Meta(FolderSerializer.Meta):
        fields = FolderSerializer.Meta.fields + ['shared_users', 'shared_users_ids']

    def update(self, instance, validated_data):
        shared_users = validated_data.pop('shared_users', None)
        folder = super().update(instance, validated_data)

        if shared_users is not None:
            folder.shared_users.set(shared_users)

        return folder


class CommentSerializer(serializers.ModelSerializer):
    user = UserMinimalSerializer(read_only=True)
    parent_id = serializers.PrimaryKeyRelatedField(
        source='parent', queryset=Comment.objects.all(),
        required=False, allow_null=True, write_only=True
    )

    class Meta:
        model = Comment
        fields = ['id', 'document', 'user', 'content', 'created_at',
                  'modified_at', 'parent', 'parent_id']
        read_only_fields = ['created_at', 'modified_at']

    def create(self, validated_data):
        validated_data['user'] = self.context['request'].user
        return super().create(validated_data)


class DocumentVersionSerializer(serializers.ModelSerializer):
    created_by = UserMinimalSerializer(read_only=True)

    class Meta:
        model = DocumentVersion
        fields = ['id', 'document', 'file', 'file_size', 'version',
                  'created_by', 'created_at', 'comment']
        read_only_fields = ['file_size', 'created_at']

    def create(self, validated_data):
        validated_data['created_by'] = self.context['request'].user

        # Set file size if file is provided
        if 'file' in validated_data:
            validated_data['file_size'] = validated_data['file'].size

        return super().create(validated_data)


class DocumentActivitySerializer(serializers.ModelSerializer):
    user = UserMinimalSerializer(read_only=True)

    class Meta:
        model = DocumentActivity
        fields = ['id', 'document', 'user', 'activity_type',
                  'description', 'created_at', 'ip_address']
        read_only_fields = ['created_at', 'ip_address']


class DocumentSerializer(serializers.ModelSerializer):
    owner = UserMinimalSerializer(read_only=True)
    tags = TagSerializer(many=True, read_only=True)
    folder_id = serializers.PrimaryKeyRelatedField(
        source='folder', queryset=Folder.objects.all(),
        required=False, allow_null=True, write_only=True
    )
    tag_ids = serializers.PrimaryKeyRelatedField(
        source='tags', queryset=Tag.objects.all(),
        many=True, required=False, write_only=True
    )

    class Meta:
        model = Document
        fields = ['id', 'title', 'description', 'file', 'file_type',
                  'file_size', 'folder', 'folder_id', 'tags', 'tag_ids',
                  'owner', 'created_at', 'modified_at', 'is_public', 'version']
        read_only_fields = ['file_size', 'file_type', 'created_at', 'modified_at', 'version']

    def create(self, validated_data):
        tags = validated_data.pop('tags', [])
        validated_data['owner'] = self.context['request'].user

        document = super().create(validated_data)

        if tags:
            document.tags.set(tags)

        # Create document activity log
        DocumentActivity.objects.create(
            document=document,
            user=self.context['request'].user,
            activity_type='created',
            description='Document created',
            ip_address=self.context['request'].META.get('REMOTE_ADDR')
        )

        # Create initial version
        if document.file:
            DocumentVersion.objects.create(
                document=document,
                file=document.file,
                file_size=document.file_size,
                version=1,
                created_by=document.owner,
                comment='Initial version'
            )

        return document


class DocumentDetailSerializer(DocumentSerializer):
    versions = DocumentVersionSerializer(many=True, read_only=True)
    comments = CommentSerializer(many=True, read_only=True)
    activities = DocumentActivitySerializer(many=True, read_only=True)
    shared_users = UserMinimalSerializer(many=True, read_only=True)
    shared_users_ids = serializers.PrimaryKeyRelatedField(
        source='shared_users', queryset=User.objects.all(),
        many=True, required=False, write_only=True
    )

    class Meta(DocumentSerializer.Meta):
        fields = DocumentSerializer.Meta.fields + [
            'versions', 'comments', 'activities',
            'shared_users', 'shared_users_ids'
        ]

    def update(self, instance, validated_data):
        tags = validated_data.pop('tags', None)
        shared_users = validated_data.pop('shared_users', None)

        # Check if new file is uploaded
        old_file = instance.file
        new_version_needed = 'file' in validated_data and validated_data['file'] != old_file

        # Update document fields
        document = super().update(instance, validated_data)

        # Update tags if provided
        if tags is not None:
            document.tags.set(tags)

        # Update shared users if provided
        if shared_users is not None:
            document.shared_users.set(shared_users)

        # Create a new version if file has changed
        if new_version_needed:
            document.version += 1
            document.save()

            DocumentVersion.objects.create(
                document=document,
                file=document.file,
                file_size=document.file_size,
                version=document.version,
                created_by=self.context['request'].user,
                comment=f'Version {document.version}'
            )

            # Log activity
            DocumentActivity.objects.create(
                document=document,
                user=self.context['request'].user,
                activity_type='updated',
                description=f'Updated to version {document.version}',
                ip_address=self.context['request'].META.get('REMOTE_ADDR')
            )

        return document