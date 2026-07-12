from django.shortcuts import render, get_object_or_404
from django.http import HttpResponse, HttpResponseRedirect, Http404
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_POST
from django.urls import reverse

from .models import TodoList, StreamerProfile

import uuid

# Basic Homepage
def index(request):
    return render(request, 'todos/index.html')

# Main dashboard
@login_required
def dashboard(request):
    # Get userprofile object if it exists
    if hasattr(request.user, "profile"):
        streamer = request.user.profile
        lists = TodoList.objects.filter(streamer=streamer)
        base_url = request.build_absolute_uri("/")
        
    # If it doesn't redirect to tutorial (Likely first launch)
    else:
        return HttpResponseRedirect(reverse("todos:tutorial"))

    context = {
        'streamer': streamer,
        'lists': lists,
        'base_url': base_url,
    }
    return render(request, 'todos/dashboard.html', context)

# Tutorial & initial settings on first launch
@login_required
def tutorial(request):
    # Redirect to dashboard if profile object already exists for user
    if hasattr(request.user, "profile"):
        return HttpResponseRedirect(reverse("todos:dashboard"))
    else:
        return render(request, 'todos/tutorial.html')
    
@login_required
@require_POST
def createProfile(request):
    user = request.user
    
    # Safe input handling; replace with defaults where possible, throw user error on incorrectly formatted inputs
    max_todos_raw = request.POST.get("max_viewer_todos", 3)
    list_title = request.POST.get("list_title", "").strip()
    try:
        max_todos = int(max_todos_raw)
    except ValueError:
        return render(request, "todos/tutorial.html", {"error_message": "Please enter a valid number."})
    if max_todos < 0 or max_todos > 10:
        return render(request, "todos/tutorial.html", {"error_message": "Please keep the maximum viewer todos between 0 and 10."})
    if not list_title:
        return render(request, "todos/tutorial.html", {"error_message": "Please enter a name for your first list."})
        
    # Create profile object & first list
    profile = StreamerProfile(
        user=user, 
        twitch_username=user.username, 
        max_viewer_todos=max_todos
    )
    profile.save()
    
    first_list = TodoList(
        streamer=profile, 
        name=list_title
    )
    first_list.save()

    return HttpResponseRedirect(reverse("todos:dashboard"))

def embed(request, user_id:uuid, todo_list:str):
    streamer = get_object_or_404(StreamerProfile, obs_token=user_id)
    if todo_list == "chatlist":
        embed_list = streamer.active_chat_list
    elif todo_list == "streamerlist":
        embed_list = streamer.active_streamer_list
    else:
        embed_list = get_object_or_404(TodoList, streamer=streamer, name=todo_list)
    if not embed_list: raise Http404("Requested list does not exist")

    return render(request, 'todos/embed.html', {"list":embed_list})