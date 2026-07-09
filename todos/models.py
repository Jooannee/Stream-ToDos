import uuid
from django.db import models
from django.contrib.auth.models import User

class StreamerProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    twitch_username = models.CharField(max_length=100, unique=True)
    obs_token = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)
    max_viewer_todos = models.IntegerField(default=3)
    
    active_streamer_list = models.ForeignKey(
        'TodoList', 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True, 
        related_name='active_for_streamer'
    )
    active_chat_list = models.ForeignKey(
        'TodoList', 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True, 
        related_name='active_for_chat'
    )

    def __str__(self):
        return self.twitch_username


class TodoList(models.Model):
    streamer = models.ForeignKey(StreamerProfile, on_delete=models.CASCADE, related_name='custom_lists')
    name = models.CharField(max_length=100)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.name} ({self.streamer.twitch_username})"


class TodoItem(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('completed', 'Completed'),
        ('archived', 'Archived'),
    ]

    todo_list = models.ForeignKey(TodoList, on_delete=models.CASCADE, related_name='items')
    creator_name = models.CharField(max_length=100) 
    title = models.CharField(max_length=255)
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='pending')
    chat_index = models.IntegerField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    completed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ['created_at']

    def save(self, *args, **kwargs):
        if not self.chat_index and self.status == 'pending':
            if self.todo_list.streamer.active_chat_list == self.todo_list:
                active_todos = TodoItem.objects.filter(
                    todo_list=self.todo_list, 
                    status='pending'
                ).count()
                self.chat_index = active_todos + 1
        super().save(*args, **kwargs)

    def __str__(self):
        return f"[{self.todo_list.name}] {self.title}"