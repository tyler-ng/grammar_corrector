import os
import uuid
from django.db import models
from django.conf import settings
from django.utils.text import slugify


def get_file_path(instance, filename):
    """Generate unique file path for uploaded documents"""
    ext = filename.split('.')[-1]
    filename = f"{uuid.uuid4()}.{ext}"
    if instance.folder:
        return os.path.join('documents', str(instance.folder.id), filename)
    return os.path.join('documents', filename)


class Folder(models.Model):
    """Folder model for organizing documents"""
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    parent = models.ForeignKey('self', on_delete=models.CASCADE,
                               null=True, blank=True, related_name='children')
    owner = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE,
                              related_name='owned_folders')
    shared_users = models.ManyToManyField(settings.AUTH_USER_MODEL,
                                          related_name='shared_folders', blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    modified_at = models.DateTimeField(auto_now=True)
    is_public = models.BooleanField(default=False)

    class Meta:
        ordering = ['-modified_at']
        unique_together = ['name', 'parent', 'owner']

    def __str__(self):
        return self.name

    @property
    def full_path(self):
        """Get the full path of the folder"""
        if self.parent:
            return os.path.join(self.parent.full_path, self.name)
        return self.name


class Tag(models.Model):
    """Tag model for categorizing documents"""
    name = models.CharField(max_length=50, unique=True)
    slug = models.SlugField(max_length=50, unique=True, editable=False)

    def save(self, *args, **kwargs):
        self.slug = slugify(self.name)
        super().save(*args, **kwargs)

    def __str__(self):
        return self.name


class Document(models.Model):
    """Document model for storing files"""
    title = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    file = models.FileField(upload_to=get_file_path)
    file_type = models.CharField(max_length=100, blank=True)
    file_size = models.PositiveIntegerField(default=0)  # in bytes
    folder = models.ForeignKey(Folder, on_delete=models.CASCADE,
                               null=True, blank=True, related_name='documents')
    tags = models.ManyToManyField(Tag, related_name='documents', blank=True)
    owner = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE,
                              related_name='owned_documents')
    shared_users = models.ManyToManyField(settings.AUTH_USER_MODEL,
                                          related_name='shared_documents', blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    modified_at = models.DateTimeField(auto_now=True)
    is_public = models.BooleanField(default=False)
    version = models.PositiveIntegerField(default=1)

    class Meta:
        ordering = ['-modified_at']

    def __str__(self):
        return self.title

    def save(self, *args, **kwargs):
        # Set file size if file is provided
        if self.file:
            self.file_size = self.file.size

            # Set file type based on extension
            file_name = self.file.name.lower()
            ext = os.path.splitext(file_name)[1]
            self.file_type = ext[1:] if ext else ''

        super().save(*args, **kwargs)


class DocumentVersion(models.Model):
    """Document version history"""
    document = models.ForeignKey(Document, on_delete=models.CASCADE, related_name='versions')
    file = models.FileField(upload_to=get_file_path)
    file_size = models.PositiveIntegerField(default=0)  # in bytes
    version = models.PositiveIntegerField()
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)
    comment = models.TextField(blank=True)

    class Meta:
        ordering = ['-version']
        unique_together = ['document', 'version']

    def __str__(self):
        return f"{self.document.title} - v{self.version}"


class DocumentActivity(models.Model):
    """Activity log for document actions"""
    ACTIVITY_TYPES = (
        ('created', 'Created'),
        ('updated', 'Updated'),
        ('deleted', 'Deleted'),
        ('accessed', 'Accessed'),
        ('shared', 'Shared'),
        ('unshared', 'Unshared'),
        ('commented', 'Commented'),
    )

    document = models.ForeignKey(Document, on_delete=models.SET_NULL,
                                 null=True, related_name='activities')
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    activity_type = models.CharField(max_length=20, choices=ACTIVITY_TYPES)
    description = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    ip_address = models.GenericIPAddressField(null=True, blank=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name_plural = 'Document activities'

    def __str__(self):
        return f"{self.user.username} {self.activity_type} {self.document.title if self.document else 'deleted document'}"


class Comment(models.Model):
    """Comments on documents"""
    document = models.ForeignKey(Document, on_delete=models.CASCADE, related_name='comments')
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    content = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    modified_at = models.DateTimeField(auto_now=True)
    parent = models.ForeignKey('self', on_delete=models.CASCADE,
                               null=True, blank=True, related_name='replies')

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"Comment by {self.user.username} on {self.document.title}"