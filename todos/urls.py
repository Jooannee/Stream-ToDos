from django.urls import path, include
from . import views

app_name = "todos"
urlpatterns = [
    # Homepage
    path('', views.index, name="index"),
    
    # Dashboard URLs
    path('dashboard/', views.dashboard, name="dashboard"),
    path('tutorial/', views.tutorial, name="tutorial"),
    path('createProfile/', views.createProfile, name="createProfile"),
]