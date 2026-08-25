from django.shortcuts import render, get_object_or_404
from django.http import HttpResponse, HttpResponseRedirect, Http404
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_POST
from django.urls import reverse

from .models import TodoList, StreamerProfile, TodoItem

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
        
    # If it doesn't redirect to tutorial (Likely first launch)
    else:
        return HttpResponseRedirect(reverse("todos:tutorial"))

    context = {
        'streamer': streamer,
        'lists': lists,
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
    streamer_list_title = request.POST.get("streamer_list_title", "").strip()
    chat_list_title = request.POST.get("chat_list_title", "").strip()
    try:
        max_todos = int(max_todos_raw)
    except ValueError:
        return render(request, "todos/tutorial.html", {"error_message": "Please enter a valid number."})
    if max_todos < 0 or max_todos > 10:
        return render(request, "todos/tutorial.html", {"error_message": "Please keep the maximum viewer todos between 0 and 10."})
    if not streamer_list_title or not chat_list_title:
        return render(request, "todos/tutorial.html", {"error_message": "Please enter names for your first lists."})
        
    # Create profile object & first lists and declare as active lists
    profile = StreamerProfile(
        user=user, 
        twitch_username=user.username, 
        max_viewer_todos=max_todos
    )
    profile.save()
    
    first_streamer_list = TodoList(
        streamer=profile, 
        name=streamer_list_title
    )
    first_chat_list = TodoList(
        streamer=profile, 
        name=chat_list_title
    )
    first_streamer_list.save()
    first_chat_list.save()

    profile.active_chat_list = first_chat_list
    profile.active_streamer_list = first_streamer_list
    profile.save()

    return HttpResponseRedirect(reverse("todos:dashboard"))

@login_required
@require_POST
def createTodo(request, todo_list:str):
    user = request.user
    streamer = user.profile
    lists = TodoList.objects.filter(streamer=streamer)
    tlist = get_object_or_404(TodoList, name=todo_list)

    todo_title = request.POST.get("title", "")
    if not todo_title:
        context = {
        'streamer': streamer,
        'lists': lists,
        'error_message': "You didn't supply a title for the todo!"
        }
        return render(request, 'todos/dashboard.html', context)
    
    new_item = TodoItem(todo_list=tlist, creator_name=streamer.twitch_username, title=todo_title)
    new_item.save()
    return HttpResponseRedirect(reverse("todos:dashboard"))



def embed(request, user_id:uuid, todo_list:str):
    streamer = get_object_or_404(StreamerProfile, obs_token=user_id)
    if todo_list == "chatlist":
        embed_list = streamer.active_chat_list
    elif todo_list == "streamerlist":
        embed_list = streamer.active_streamer_list
    else:
        embed_list = get_object_or_404(TodoList, streamer=streamer, safe_name=todo_list)
    if not embed_list: raise Http404("Requested list does not exist")

    theme = streamer.active_theme

    return render(request, 'todos/embed.html', {"list":embed_list, "streamer": streamer, "theme":theme})

@login_required
def settings(request):
    return render(request, 'todos/settings.html')
@login_required
@require_POST
def changeSettings(request):
    tta = request.POST.get("tta", "")
    max_todos = request.POST.get("max_viewer_todos", "")

    try:
        tta = int(tta)
        max_todos = int(max_todos)
    except ValueError:
        return render(request, 'todos/settings.html', {"error_message": "Please enter numbers"})

    streamer = request.user.profile
    streamer.time_to_archive = tta
    streamer.max_viewer_todos = max_todos
    streamer.save()
    return HttpResponseRedirect(reverse("todos:dashboard"))