from django.contrib import admin

from .models import SSHKey


class SSHKeyAdmin(admin.ModelAdmin):
    list_display = ('key_type', 'active', 'user', 'key_type', 'system')


admin.site.register(SSHKey, SSHKeyAdmin)
