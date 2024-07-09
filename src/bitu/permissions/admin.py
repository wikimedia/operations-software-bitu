from django.contrib import admin

from .models import PermissionRequest, Log


class PermissionRequestAdmin(admin.ModelAdmin):
    list_display = ['user', 'system', 'key', 'status']


class LogAdmin(admin.ModelAdmin):
    list_display = ['created', 'created_by']


admin.site.register(Log, LogAdmin)
admin.site.register(PermissionRequest, PermissionRequestAdmin)
