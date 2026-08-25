from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from asgiref.sync import async_to_sync

from channels.layers import get_channel_layer

from .models import TodoItem, TodoList, StreamerProfile
from allauth.socialaccount.models import SocialToken

@receiver(post_save, sender=TodoItem)
@receiver(post_delete, sender=TodoItem)
def todo_item_change(sender, instance:TodoItem, **kwargs):
    channel_layer = get_channel_layer()
    if not channel_layer:
        return
    
    todo_list:TodoList = instance.todo_list
    streamer:StreamerProfile = todo_list.streamer
    obs_token = str(streamer.obs_token)

    groups_to_notify = [
        f"todo_{obs_token}_{todo_list.safe_name}",
        f"dashboard_{streamer.user.username.lower()}"
    ]
    if streamer.active_chat_list_id == todo_list.id:
        groups_to_notify.append(f"todo_{obs_token}_chatlist")
    if streamer.active_streamer_list_id == todo_list.id:
        groups_to_notify.append(f"todo_{obs_token}_streamerlist")
    
    for group_name in groups_to_notify:
        async_to_sync(channel_layer.group_send)(
            group_name,
            {
                "type": "todo_update",
                "obs_token": obs_token,
                "updated_list": todo_list.safe_name
            }
        )

@receiver(post_delete, sender=TodoList)
def todo_list_change(sender, instance:TodoList, **kwargs):
    channel_layer = get_channel_layer()
    if not channel_layer:
        return

    streamer:StreamerProfile = instance.streamer
    async_to_sync(channel_layer.group_send)(
        f"dashboard_{streamer.user.username.lower()}",
        {
            "type": "list_update",
            "created": False,
            "deleted": True,
            "updated_list": instance.safe_name
        }
    )

@receiver(post_save, sender=StreamerProfile)
def streamer_profile_change(sender, instance, **kwargs):
    channel_layer = get_channel_layer()
    if not channel_layer:
        return
    
    obs_token = str(instance.obs_token)

    for alias in ["chatlist", "streamerlist"]:
        group_name = f"todo_{obs_token}_{alias}"
        async_to_sync(channel_layer.group_send)(
            group_name,
            {
                "type": "todo_update"
            }
        )