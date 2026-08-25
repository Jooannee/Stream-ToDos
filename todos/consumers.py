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
        match text_data_json["type"]:
            case "mark_done":
                listName = text_data_json["list"]
                itemIndex = text_data_json["item"]
                try:
                    await self.toggle_item_complete(str(self.scope["user"]), listName, itemIndex)
                    await self.send(text_data=json.dumps({
                        "type": "success",
                        "message": "Item marked complete"
                    }))
                except Exception as e:
                    await self.send(text_data=json.dumps({
                        "type": "error",
                        "message": str(e)
                    }))

            case "new_list":
                list_name = text_data_json["list_name"]
                try: 
                    await self.create_new_list(str(self.scope["user"]), list_name)
                    await self.send(text_data=json.dumps({
                    "type": "success",
                    "message": "New List created"
                    }))
                except Exception as e:
                    await self.send(text_data=json.dumps({
                        "type": "error",
                        "message": str(e)
                    }))
                
            case _:
                pass

    @database_sync_to_async
    def toggle_item_complete(self, username, listName, itemIndex):
        try:
            streamer = StreamerProfile.objects.get(twitch_username=username)
            tList = TodoList.objects.get(streamer=streamer, name=listName)
            tItem = TodoItem.objects.get(todo_list=tList, chat_index=itemIndex)

            if tItem.status == "completed":
                tItem.status = "pending"
                tItem.completed_at = None
            else:
                tItem.status = "completed"

            tItem.save()
        except Exception as e:
            raise e
    @database_sync_to_async
    def create_new_list(self, username, list_name):
        try:
            streamer = StreamerProfile.objects.get(twitch_username=username)
            curr_lists = TodoList.objects.filter(streamer=streamer)
            curr_list_names = curr_lists.values_list("name", flat=True)

            if not list_name:
                raise TypeError("Missing List Name")
            if list_name in curr_list_names:
                raise ValueError("Already have a List with that name")
            if list_name in ["chatlist", "streamerlist"]:
                raise ValueError("List name unallowed")

            new_list = TodoList(streamer=streamer, name=list_name)
            new_list.save()
        except Exception as e:
            raise e
            