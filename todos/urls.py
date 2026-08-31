from django.urls import path, include
from . import views

app_name = "todos"
urlpatterns = [
    # Homepage
    path('', views.index, name="index"),
    path('imprint/', views.imprint, name="imprint"),
    path('impressum/', views.imprint, name="impressum"),
    
    # Dashboard URLs
    path('dashboard/', views.dashboard, name="dashboard"),
    path('tutorial/', views.tutorial, name="tutorial"),
    path('settings/', views.settings, name="settings"), 

    # POST URLs
    path('createProfile/', views.createProfile, name="createProfile"),
    path('changeSettings', views.changeSettings, name="changeSettings"),

    # OBS Source
    path('embed/<uuid:user_id>/<str:todo_list>/', views.embed, name="embed")
]