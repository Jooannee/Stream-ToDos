import json

from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from django.template.loader import render_to_string
from todos.models import StreamerProfile, TodoList, TodoItem
from django.core.exceptions import ObjectDoesNotExist

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
                embed_list = TodoList.objects.get(streamer=streamer, safe_name=self.todo_list)

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
                    embed_list = TodoList.objects.get(streamer=streamer, safe_name=self.todo_list)
                
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
        except ValueError:
            pass
        except Exception as e:
            await self.send(text_data=json.dumps({
                "type": "error",
                "message": str(e)
            }))

    async def list_update(self, event):
        updated_list_safe = event["updated_list"]
        if event["deleted"]:
            await self.send(text_data=json.dumps({
            "type": "list_delete",
            "list": updated_list_safe
            }))
            return

    @database_sync_to_async
    def get_streamer(self, obs_token):
        return StreamerProfile.objects.get(obs_token=obs_token)
    @database_sync_to_async
    def get_streamer_by_name(self, streamerName):
        return StreamerProfile.objects.get(twitch_username=streamerName)
    @database_sync_to_async
    def get_list(self, safe_name, streamer):
        try:
            return TodoList.objects.get(safe_name=safe_name, streamer=streamer)
        except ObjectDoesNotExist:
            raise ValueError("List does not exist. Likely just deleted")
        except Exception as e:
            raise e
    @database_sync_to_async
    def get_list_unsafe(self, name, streamer):
        try:
            return TodoList.objects.get(name=name, streamer=streamer)
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
                    new_list = await self.create_new_list(str(self.scope["user"]), list_name)
                    await self.send(text_data=json.dumps({
                    "type": "success",
                    "message": f"New List created: {list_name}"
                    }))
                    html = await self.get_html_dash(await self.get_list_unsafe(list_name, await self.get_streamer_by_name(str(self.scope["user"]))))
                    await self.send(text_data=json.dumps({
                        "type": "list_create",
                        "list": new_list.safe_name,
                        "html": html
                    }))
                except Exception as e:
                    await self.send(text_data=json.dumps({
                        "type": "error",
                        "message": str(e)
                    }))

            case "delete_list":
                list_name = text_data_json["list_name"]
                try: 
                    await self.delete_list(str(self.scope["user"]), list_name)
                    await self.send(text_data=json.dumps({
                    "type": "success",
                    "message": f"List deleted: {list_name}"
                    }))
                except Exception as e:
                    await self.send(text_data=json.dumps({
                        "type": "error",
                        "message": str(e)
                    }))

            case "set_chat_list":
                list_name = text_data_json["list_name"]
                try: 
                    await self.set_chat_list(str(self.scope["user"]), list_name)
                    await self.send(text_data=json.dumps({
                    "type": "success",
                    "message": f"Chatlist set: {list_name}"
                    }))
                    streamer = await self.get_streamer_by_name(str(self.scope["user"]))
                    lists = await self.get_streamer_lists(streamer)
                    for l in lists:
                        await self.channel_layer.group_send(
                            self.group_name,
                            {
                                "type": "todo_update",
                                "obs_token": str(streamer.obs_token),
                                "updated_list": l.safe_name
                            }
                        )
                except Exception as e:
                    await self.send(text_data=json.dumps({
                        "type": "error",
                        "message": str(e)
                    }))

            case "set_streamer_list":
                list_name = text_data_json["list_name"]
                try: 
                    await self.set_streamer_list(str(self.scope["user"]), list_name)
                    await self.send(text_data=json.dumps({
                    "type": "success",
                    "message": f"Streamerlist set: {list_name}"
                    }))
                    streamer = await self.get_streamer_by_name(str(self.scope["user"]))
                    lists = await self.get_streamer_lists(streamer)
                    for l in lists:
                        await self.channel_layer.group_send(
                            self.group_name,
                            {
                                "type": "todo_update",
                                "obs_token": str(streamer.obs_token),
                                "updated_list": l.safe_name
                            }
                        )
                except Exception as e:
                    await self.send(text_data=json.dumps({
                        "type": "error",
                        "message": str(e)
                    }))

            case "new_item":
                list_name = text_data_json["list_name"]
                item_name = text_data_json["item_name"]

                try:
                    await self.create_new_item(str(self.scope["user"]), list_name, item_name)
                    await self.send(text_data=json.dumps({
                    "type": "success",
                    "message": f"New item: {item_name}"
                    }))
                except Exception as e:
                    await self.send(text_data=json.dumps({
                        "type": "error",
                        "message": str(e)
                    }))

                
            case _:
                await self.send(text_data=json.dumps({
                    "type": "error",
                    "message": "Unexpected Websocket funtion"
                }))

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
            return new_list
        except Exception as e:
            raise e
    @database_sync_to_async
    def delete_list(self, username, list_name):
        try:
            streamer = StreamerProfile.objects.get(twitch_username=username)
            list_object = TodoList.objects.get(streamer=streamer, name=list_name)
            list_object.delete()
        except Exception as e:
            raise e
    @database_sync_to_async
    def set_chat_list(self, username, list_name):
        try:
            streamer = StreamerProfile.objects.get(twitch_username=username)
            list_object = TodoList.objects.get(streamer=streamer, name=list_name)

            streamer.active_chat_list = list_object
            streamer.save()
        except Exception as e:
            raise e
    @database_sync_to_async
    def set_streamer_list(self, username, list_name):
        try:
            streamer = StreamerProfile.objects.get(twitch_username=username)
            list_object = TodoList.objects.get(streamer=streamer, name=list_name)

            streamer.active_streamer_list = list_object
            streamer.save()
        except Exception as e:
            raise e
    @database_sync_to_async
    def create_new_item(self, username, list_name, item_name):
        try:
            streamer = StreamerProfile.objects.get(twitch_username=username)
            list_object = TodoList.objects.get(streamer=streamer, name=list_name)

            if not item_name:
                raise ValueError("Missing item name")

            new_item = TodoItem(todo_list=list_object, creator_name=username, title=item_name, status="pending")
            new_item.save()
        except Exception as e:
            raise e
    @database_sync_to_async
    def get_streamer_lists(self, streamer):
        return list(TodoList.objects.filter(streamer=streamer))