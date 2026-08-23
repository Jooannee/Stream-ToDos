import json

from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from django.template.loader import render_to_string
from todos.models import StreamerProfile, TodoList, TodoItem

from django.core.exceptions import ObjectDoesNotExist, MultipleObjectsReturned

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
        html = await self.get_updated_html_embed()
        await self.send(text_data=json.dumps({
            "type": "todo_update",
            "todo_title": title,
            "html": html
        }))
    
    @database_sync_to_async
    def get_updated_html_embed(self):
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

class DashConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        user = self.scope["user"]
        if str(user) == "AnonymousUser":
            await self.close()
        else:
            self.group_name = f"dashboard_{str(user).lower()}"
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
        updated_list_safe = event["updated_list"]
        streamer = await self.get_streamer(event["obs_token"])
        
        try:
            list_object = await self.get_list(updated_list_safe, streamer)
            html = await self.get_html_dash(list_object)

            await self.send(text_data=json.dumps({
            "type": "list_update",
            "list": updated_list_safe,
            "html": html
            }))
            
        except ObjectDoesNotExist:
            await self.send(text_data=json.dumps({
            "type": "list_delete",
            "list": updated_list_safe
            }))
        except MultipleObjectsReturned:
            pass
            """TODO: DO SOMETHING HERE XD"""

    @database_sync_to_async
    def get_streamer(self, obs_token):
        return StreamerProfile.objects.get(obs_token=obs_token)
    @database_sync_to_async
    def get_list(self, safe_name, streamer):
        try:
            return TodoList.objects.get(safe_name=safe_name, streamer=streamer)
        except Exception as e:
            raise e
    @database_sync_to_async
    def get_html_dash(self, list_object):
        return render_to_string("todos/dash_list_partial.html", {"tlist":list_object})

    async def receive(self, text_data = None, bytes_data = None):
        text_data_json = json.loads(text_data)
        print(text_data_json)
        match text_data_json["type"]:
            case "mark_done":
                print("here")
                listName = text_data_json["list"]
                itemName = text_data_json["item"]
                await self.set_item_complete(str(self.scope["user"]), listName, itemName)

            case _:
                pass

    @database_sync_to_async
    def set_item_complete(self, userName, listName, itemName):
        print("here3")
        try:
            print("here2")
            streamer = StreamerProfile.objects.get(twitch_username=userName)
            tList = TodoList.objects.get(streamer=streamer, name=listName)
            tItem = TodoItem.objects.get(todo_list=tList, title=itemName)

            tItem.status = "completed"
            tItem.save()
        except Exception as e:
            print(e)