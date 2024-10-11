from django.contrib import admin

from .models import UserBlockEventLog


class UserBlockEventLogAdmin(admin.ModelAdmin):
    list_display = ['username', 'action', 'created_by', 'created_at']
    readonly_fields = ['username', 'action', 'created_by', 'created_at', 'comment', 'parent']


admin.site.register(UserBlockEventLog, UserBlockEventLogAdmin)
