# SPDX-License-Identifier: GPL-3.0-or-later
from django.contrib import admin
from django.contrib.auth.admin import UserAdmin

from .models import User, Token, SecurityToken


class AccountUserAdmin(UserAdmin):
    pass


class TokenAdmin(admin.ModelAdmin):
    list_display = ('created', 'user', 'comment')


class SecurityTokenAdmin(admin.ModelAdmin):
    list_display = ('user', 'created', 'enabled')
    readonly_fields = ('user', 'created', 'enabled')
    exclude = ('secret',)


admin.site.register(SecurityToken, SecurityTokenAdmin)
admin.site.register(Token, TokenAdmin)
admin.site.register(User, AccountUserAdmin)
