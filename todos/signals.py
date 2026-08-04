from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from asgiref.sync import async_to_sync

from channels.layers import get_channel_layer

from .models import TodoItem, TodoList, StreamerProfile
from allauth.socialaccount.models import SocialToken

@receiver(post_save, sender=TodoItem)
@receiver(post_delete, sender=TodoItem)
def todo_item_change(sender, instance, **kwargs):
    channel_layer = get_channel_layer()
    if not channel_layer:
        return
    
    todo_list:TodoList = instance.todo_list
    streamer:StreamerProfile = todo_list.streamer
    obs_token = str(streamer.obs_token)

    groups_to_notify = [
        f"todo_{obs_token}_{todo_list.safe_name}"
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


@receiver(post_save, sender=SocialToken)
def token_changed(sender, instance:SocialToken, created:bool, **kwargs):
    if not created:
        return
    
    channel_layer = get_channel_layer()
    if not channel_layer:
        return
    
    token = instance.token
    refresh = instance.token_secret
    twitch_uid = instance.account.uid

    async_to_sync(channel_layer.group_send)(
        "user_register",
        {
            "type": "user_register",
            "token": token,
            "refresh": refresh,
            "twitch_uid": twitch_uid
        }
    )
    print("reached1")