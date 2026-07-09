from django.contrib import admin

from .models import StreamerProfile, TodoList, TodoItem
# Register your models here.

class TodoItemInline(admin.TabularInline):
    model = TodoItem
    extra = 1
    exclude = ("chat_index",)

class TodoListAdmin(admin.ModelAdmin):
    fieldsets = [
        (None, {"fields": ["streamer", "name"]})
    ]
    inlines = [TodoItemInline]

admin.site.register(StreamerProfile)
admin.site.register(TodoList, TodoListAdmin)

