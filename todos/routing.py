from django.urls import path
from . import consumers

websocket_urlpatterns = [
    path('ws/todo/<uuid:user_id>/<str:todo_list>/', consumers.TodoConsumer.as_asgi()),
    path('ws/dash/', consumers.DashConsumer.as_asgi()),
]