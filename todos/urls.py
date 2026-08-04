from django.urls import path, include
from . import views

app_name = "todos"
urlpatterns = [
    # Homepage
    path('', views.index, name="index"),
    
    # Dashboard URLs
    path('dashboard/', views.dashboard, name="dashboard"),
    path('tutorial/', views.tutorial, name="tutorial"),
    path('settings/', views.settings, name="settings"), 

    # POST URLs
    path('createProfile/', views.createProfile, name="createProfile"),
    path('list/create-list', views.createList, name="createList"),
    path('list/delete-list', views.deleteList, name="deleteList"),
    path('list/<str:todo_list>/create-todo', views.createTodo, name="createTodo"),
    path('list/set-chat-list', views.setChatList, name="setChatList"),
    path('list/set-streamer-list', views.setStreamerList, name="setStreamerList"),
    path('changeSettings', views.changeSettings, name="changeSettings"),

    # OBS Source
    path('embed/<uuid:user_id>/<str:todo_list>/', views.embed, name="embed")
]