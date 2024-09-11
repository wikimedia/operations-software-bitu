from django.contrib import admin

from .models import PermissionRequest, Log


class PermissionRequestAdmin(admin.ModelAdmin):
    list_display = ['user', 'system', 'key', 'status']
    readonly_fields = ['user', 'system', 'key', 'status', 'comment', 'ticket']


class LogAdmin(admin.ModelAdmin):
    list_display = ['created', 'created_by', 'user']
    readonly_fields = ['created', 'created_by', 'approved', 'comment', 'request']

    def user(self, obj):
        return obj.request.user


admin.site.register(Log, LogAdmin)
admin.site.register(PermissionRequest, PermissionRequestAdmin)
