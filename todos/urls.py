from django.urls import path, include
from . import views

app_name = "todos"
urlpatterns = [
    # Homepage
    path('', views.index, name="index"),
    
    # Dashboard URLs
    path('dashboard/', views.dashboard, name="dashboard"),
    path('tutorial/', views.tutorial, name="tutorial"),

    # POST URLs
    path('createProfile/', views.createProfile, name="createProfile"),
    path('list/create-list', views.createList, name="createList"),

    # OBS Source
    path('embed/<uuid:user_id>/<str:todo_list>/', views.embed, name="embed")
]