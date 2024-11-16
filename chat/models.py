from django.db import models
from django.contrib.auth import get_user_model
import uuid
from datetime import datetime

User = get_user_model()

# Create your models here.
class Profile(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    external_id = models.IntegerField(null=True, blank=True)  # Changed id_user to external_id for clarity
    bio = models.TextField(blank=True, null=True)
    profileimg = models.ImageField(upload_to='profile_images', default='blank-profile-picture.png')
    location = models.CharField(max_length=100, blank=True, null=True)

    def __str__(self):
        return self.user.username

class Post(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    image = models.ImageField(upload_to='post_images')
    caption = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    no_of_likes = models.IntegerField(default=0)  # Consider using ManyToMany for likes

    def __str__(self):
        return f"Post by {self.user}"

class LikePost(models.Model):
    post = models.ForeignKey(Post, on_delete=models.CASCADE, null=True)  # Changed from CharField to ForeignKey
    user = models.ForeignKey(User, on_delete=models.CASCADE, null=True)

    def __str__(self):
        return self.username

class FollowersCount(models.Model):
    follower = models.ForeignKey(User, related_name='following', on_delete=models.CASCADE)
    user = models.ForeignKey(User, related_name='followers', on_delete=models.CASCADE)

    def __str__(self):
        return f"{self.follower.username} follows {self.user.username}"

class Notification(models.Model):
    NOTIFICATION_TYPES = (
        ('follow', 'Follow'),
        ('like', 'Like'),
        ('message', 'Message'),
        ('other', 'Other'),
    )
    
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='notifications')
    type = models.CharField(max_length=20, choices=NOTIFICATION_TYPES)
    message = models.TextField(null=True, blank=True)  # Custom message for "other" type
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user.username} - {self.get_type_display()} notification"
    
    def get_message(self):
        """
        Returns the message to display based on the notification type.
        """
        if self.type == 'follow':
            return f"{self.user.username} started following you."
        elif self.type == 'like':
            return f"{self.user.username} liked your post."
        elif self.type == 'message':
            return f"{self.user.username} sent you a message."
        return self.message  # For other types of notifications

    def mark_as_read(self):
        """
        Marks the notification as read.
        """
        self.is_read = True
        self.save()

class Message(models.Model):
    sender = models.ForeignKey(User, on_delete=models.CASCADE, related_name='sent_messages')
    receiver = models.ForeignKey(User, on_delete=models.CASCADE, related_name='received_messages')
    content = models.TextField()
    timestamp = models.DateTimeField(default=datetime.now, blank=True)
    is_read = models.BooleanField(default=False)  # Added field to track message read status

    def __str__(self):
        return f"{self.sender} -> {self.receiver}: {self.content}"
