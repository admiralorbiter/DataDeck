from django.db import models
import uuid
from django.db.models.signals import pre_delete
from django.dispatch import receiver
import os
from django.utils import timezone
from datetime import timedelta
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.contrib.auth.models import AbstractUser

from datadeck import settings

class Session(models.Model):
    name = models.CharField(max_length=100)
    original_name = models.CharField(max_length=100, null=True, blank=True)  # To store the original name when archived
    session_code = models.CharField(max_length=8, unique=True, editable=False)
    section = models.IntegerField()

    MODULE_CHOICES = [
        ('4', 'Module 4: Think Like a Data Scientist'),
        ('2', 'Module 3: Classroom Census'),
    ]
    module = models.CharField(
        max_length=20,
        choices=MODULE_CHOICES,
        default='4'
    )

    def clean(self):
        if self.section < 0:
            raise ValidationError("Section number cannot be negative.")
        
        # Only check for duplicate names when unarchiving or creating new sessions
        if not self.is_archived:
            existing_session = Session.objects.filter(
                created_by=self.created_by,
                section=self.section,  # Check section instead of name
                is_archived=False
            ).exclude(pk=self.pk).first()
            
            if existing_session:
                raise ValidationError(f"An active session already exists for Hour {self.section}. Cannot have multiple active sessions for the same hour.")

    def save(self, *args, **kwargs):
        if not self.session_code:
            self.session_code = uuid.uuid4().hex[:8].upper()
        
        # Skip validation if the session is being archived/unarchived
        skip_validation = kwargs.pop('skip_validation', False)
        if not skip_validation:
            self.full_clean()
        
        super().save(*args, **kwargs)

    created_at = models.DateTimeField(auto_now_add=True)
    is_paused = models.BooleanField(default=False)
    created_by = models.ForeignKey('CustomAdmin', on_delete=models.SET_NULL, blank=True, null=True)
    character_set = models.CharField(max_length=50, default='marvel')
    is_archived = models.BooleanField(default=False)
    archived_at = models.DateTimeField(null=True, blank=True)

    def is_expired(self):
        return not self.is_paused and (timezone.now() > self.created_at + timedelta(days=7))
    
    def days_until_deletion(self):
        if self.is_paused:
            return 'Paused'
        days_left = 360 - (timezone.now() - self.created_at).days
        return max(0, days_left)

    def __str__(self):
        return self.name

    def archive(self):
        self.original_name = self.name
        self.name = f"{self.name} (Archived {timezone.now().strftime('%Y-%m-%d')})"
        self.is_archived = True
        self.archived_at = timezone.now()
        # Skip validation when archiving
        self.save(skip_validation=True)

    def unarchive(self):
        # First check if there's an active session with the same section
        existing_active = Session.objects.filter(
            created_by=self.created_by,
            section=self.section,
            is_archived=False
        ).exclude(pk=self.pk).exists()

        if existing_active:
            raise ValidationError(f"Cannot unarchive - Hour {self.section} already has an active session.")

        if self.original_name:
            self.name = self.original_name
            self.original_name = None
        self.is_archived = False
        self.archived_at = None
        # Skip validation when unarchiving
        self.save(skip_validation=True)

class CustomAdmin(AbstractUser):
    school = models.CharField(max_length=100, null=True, blank=True)
    district = models.ForeignKey('District', on_delete=models.PROTECT, null=True, blank=True)
    first_name = models.CharField(max_length=100, null=True, blank=True)
    last_name = models.CharField(max_length=100, null=True, blank=True)
    media_password = models.CharField(max_length=100, blank=True, null=True)
    profile_picture = models.CharField(max_length=255, blank=True, null=True)

    groups = models.ManyToManyField(
        'auth.Group',
        related_name='custom_admin_set',
        blank=True,
        verbose_name='groups',
        help_text='The groups this user belongs to.',
    )
    user_permissions = models.ManyToManyField(
        'auth.Permission',
        related_name='custom_admin_set',
        blank=True,
        verbose_name='user permissions',
        help_text='Specific permissions for this user.',
    )

    def __str__(self):
        return f"{self.username} - {self.school} ({self.district})"

class Student(models.Model):
    name = models.CharField(max_length=100)
    password = models.CharField(max_length=100)
    section = models.ForeignKey(Session, on_delete=models.CASCADE, related_name='students')
    admin = models.ForeignKey(CustomAdmin, on_delete=models.CASCADE)
    device_id = models.CharField(max_length=255, blank=True, null=True)
    character_description = models.TextField(blank=True, null=True)
    avatar_image_path = models.CharField(max_length=255, blank=True, null=True)

    def __str__(self):
        return f"{self.name} ({self.section})"

    def get_media_interaction(self, media):
        return self.media_interactions.filter(media=media).first()

class Media(models.Model):
    MEDIA_TYPE_CHOICES = (
        ('video', 'Video'),
        ('image', 'Image'),
        ('comment', 'Comment'),
    )
    session = models.ForeignKey(Session, related_name='media', on_delete=models.CASCADE)
    title = models.CharField(max_length=100)
    description = models.TextField(null=True, blank=True)
    media_type = models.CharField(max_length=10, choices=MEDIA_TYPE_CHOICES)
    video_file = models.FileField(upload_to='videos', blank=True, null=True)
    image_file = models.ImageField(upload_to='images', blank=True, null=True)
    uploaded_at = models.DateTimeField(auto_now_add=True)
    
    # New fields for likes
    graph_likes = models.PositiveIntegerField(default=0)
    eye_likes = models.PositiveIntegerField(default=0)
    read_likes = models.PositiveIntegerField(default=0)

    GRAPH_TAG_CHOICES = [
        ('box', 'Box Plot'),
        ('histogram', 'Histogram'),
        ('comparison', 'Comparison'),
    ]
    VARIABLE_TAG_CHOICES = [
        ('gender', 'Gender'),
        ('languages', 'Languages'),
        ('handedness', 'Handedness'),
        ('eye_color', 'Eye Color'),
        ('hair_color', 'Hair Color'),
        ('hair_type', 'Hair Type'),
        ('height', 'Height'),
        ('left_foot_length', 'Left Foot Length'),
        ('right_foot_length', 'Right Foot Length'),
        ('longer_foot', 'Longer Foot'),
        ('index_finger', 'Index Finger'),
        ('ring_finger', 'Ring Finger'),
        ('longer_finger', 'Longer Finger'),
        ('arm_span', 'Arm Span'),
        ('travel_method', 'Travel Method to School'),
        ('bed_time', 'Bed Time'),
        ('wake_time', 'Wake Time'),
        ('sport_activity', 'Sport or Activity'),
        ('youtube', 'YouTube'),
        ('instagram', 'Instagram'),
        ('snapchat', 'Snapchat'),
        ('facebook', 'Facebook'),
        ('twitter', 'Twitter'),
        ('tiktok', 'TikTok'),
        ('twitch', 'Twitch'),
        ('pinterest', 'Pinterest'),
        ('bereal', 'BeReal'),
        ('whatsapp', 'WhatsApp'),
        ('discord', 'Discord'),
        ('screen_time', 'Screen Time After School'),
        ('pineapple_pizza', 'Pineapple on Pizza'),
        ('ice_cream', 'Ice Cream'),
        ('cats_or_dogs', 'Cats or Dogs'),
        ('happiness', 'Happiness'),
        ('climate_change', 'Climate Change'),
        ('reaction_time', 'Reaction Time'),
        ('memory_test', 'Memory Test'),
        ('sleep_total', 'Sleep Total'),
        ('time_to_school', 'Time to School')
    ]

    # Use CharField for specific graph types
    graph_tag = models.CharField(max_length=50, choices=GRAPH_TAG_CHOICES, blank=True, null=True)
    # Use BooleanField for general graph indicator
    is_graph = models.BooleanField(default=False)
    variable_tag = models.CharField(max_length=50, choices=VARIABLE_TAG_CHOICES, blank=True, null=True)

    submitted_password = models.CharField(max_length=100, blank=True, null=True)

    student = models.ForeignKey(Student, on_delete=models.SET_NULL, null=True, blank=True, related_name='posted_media')
    posted_by_admin = models.ForeignKey(CustomAdmin, on_delete=models.SET_NULL, null=True, blank=True, related_name='posted_media')

    project_group = models.UUIDField(null=True, blank=True)

    project_images = models.JSONField(null=True, blank=True)  # Store complete URLs
    is_project = models.BooleanField(default=False)

    def clean(self):
        if self.media_type == 'video' and self.image_file:
            raise ValidationError('Cannot upload an image file for a video media type')
        if self.media_type == 'image' and self.video_file:
            raise ValidationError('Cannot upload a video file for an image media type')

    def __str__(self):
        return self.title

    def comment_count(self):
        return self.comments.count()

    class Meta:
        ordering = ['-uploaded_at']
        indexes = [
            models.Index(fields=['session', '-uploaded_at']),
            models.Index(fields=['media_type']),
            models.Index(fields=['graph_tag']),
            models.Index(fields=['variable_tag']),
        ]

    def graph_likes_count(self):
        return self.student_interactions.filter(liked_graph=True).count()

    def eye_likes_count(self):
        return self.student_interactions.filter(liked_eye=True).count()

    def read_likes_count(self):
        return self.student_interactions.filter(liked_read=True).count()

    def get_all_images(self):
        """Return a list of all image URLs for this media item"""
        images = []
        if self.image_file:
            images.append(self.image_file.url)
        if self.project_images:
            # Make sure project_images contains complete URLs
            images.extend(self.project_images)
        return images

@receiver(pre_delete, sender=Session)
def delete_associated_media(sender, instance, **kwargs):
    media_files = instance.media.all()
    print(f"Found {media_files.count()} media files associated with the session")
    for media in media_files:
        if media.media_type == 'video' and media.video_file:
            print(f"Deleting video file: {media.video_file.path}")
            if os.path.isfile(media.video_file.path):
                try:
                    os.remove(media.video_file.path)
                    print(f"Successfully deleted video file: {media.video_file.path}")
                except Exception as e:
                    print(f"Error deleting video file {media.video_file.path}: {e}")
            else:
                print(f"Video file does not exist: {media.video_file.path}")
        elif media.media_type == 'image' and media.image_file:
            print(f"Deleting image file: {media.image_file.path}")
            if os.path.isfile(media.image_file.path):
                try:
                    os.remove(media.image_file.path)
                    print(f"Successfully deleted image file: {media.image_file.path}")
                except Exception as e:
                    print(f"Error deleting image file {media.image_file.path}: {e}")
            else:
                print(f"Image file does not exist: {media.image_file.path}")
        media.delete()

class StudentMediaInteraction(models.Model):
    student = models.ForeignKey(Student, on_delete=models.CASCADE, related_name='media_interactions')
    media = models.ForeignKey(Media, on_delete=models.CASCADE, related_name='student_interactions')
    liked_graph = models.BooleanField(default=False)
    liked_eye = models.BooleanField(default=False)
    liked_read = models.BooleanField(default=False)
    comment_count = models.PositiveIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ('student', 'media')
        indexes = [
            models.Index(fields=['student', 'media']),
        ]

    def __str__(self):
        return f"{self.student.name} - {self.media.title} Interaction"

class Comment(models.Model):
    media = models.ForeignKey(Media, related_name='comments', on_delete=models.CASCADE)
    parent = models.ForeignKey('self', null=True, blank=True, related_name='replies', on_delete=models.CASCADE)
    text = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    name = models.CharField(max_length=100)
    device_id = models.CharField(max_length=255, blank=True, null=True)
    is_admin = models.BooleanField(default=False)
    student = models.ForeignKey(Student, on_delete=models.SET_NULL, null=True, blank=True, related_name='comments')
    admin_avatar = models.CharField(max_length=255, blank=True, null=True)  # New field for admin avatar
    
    def __str__(self):
        return f'Comment by {self.name} on {self.media.title}'

    def get_avatar(self):
        if self.is_admin:
            return self.admin_avatar
        elif self.student:
            return self.student.avatar_image_path
        else:
            return None  # Or a default avatar path

class District(models.Model):
    name = models.CharField(max_length=100, unique=True)
    code = models.CharField(max_length=20, unique=True)
    created_at = models.DateTimeField(auto_now_add=True)
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return self.name

    class Meta:
        ordering = ['name']

class Observer(models.Model):
    name = models.CharField(max_length=100)
    password = models.CharField(max_length=100)
    district = models.ForeignKey(District, on_delete=models.PROTECT)
    email = models.EmailField(unique=True)
    created_at = models.DateTimeField(auto_now_add=True)
    is_active = models.BooleanField(default=True)
    created_by = models.ForeignKey('CustomAdmin', on_delete=models.SET_NULL, null=True)

    def __str__(self):
        return f"Observer: {self.name} - {self.district.name}"

    def can_view_session(self, session):
        """
        Check if observer has permission to view a specific session
        based on district matching
        """
        return session.created_by.district == self.district
