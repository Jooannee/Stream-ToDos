import json

from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from django.template.loader import render_to_string
from todos.models import StreamerProfile, TodoList

class TodoConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.user_id = str(self.scope["url_route"]["kwargs"]["user_id"])
        self.todo_list = str(self.scope["url_route"]["kwargs"]["todo_list"])
        self.group_name = f"todo_{self.user_id}_{self.todo_list}"

        await self.channel_layer.group_add(
            self.group_name,
            self.channel_name
        )

        await self.accept()
    async def disconnect(self, code):
        await self.channel_layer.group_discard(
            self.group_name,
            self.channel_name
        )

    async def todo_update(self, event):
        title = await self.get_updated_title()
        title = title if title else "???"
        html = await self.get_updated_html()
        await self.send(text_data=json.dumps({
            "type": "todo_update",
            "todo_title": title,
            "html": html
        }))
    
    @database_sync_to_async
    def get_updated_html(self):
        try:
            streamer = StreamerProfile.objects.get(obs_token=self.user_id)
            if self.todo_list == "chatlist":
                embed_list = streamer.active_chat_list
            elif self.todo_list == "streamerlist":
                embed_list = streamer.active_streamer_list
            else:
                embed_list = TodoList.objects.get(streamer=streamer, name=self.todo_list)

            if not embed_list:
                return "<div class=\"empty-state\"> List not Found <div>"
            
            return render_to_string("todos/todo_items_partial.html", {"list": embed_list})
        
        except Exception as e:
            return f"<div class=\"empty state\"> Error loading list: {str(e)}<div>"
    
    @database_sync_to_async
    def get_updated_title(self):
            try:
                streamer = StreamerProfile.objects.get(obs_token=self.user_id)
                if self.todo_list == "chatlist":
                    embed_list = streamer.active_chat_list
                elif self.todo_list == "streamerlist":
                    embed_list = streamer.active_streamer_list
                else:
                    embed_list = TodoList.objects.get(streamer=streamer, name=self.todo_list)
                
                if not embed_list:
                    return
            except:
                return
            return embed_list.name