# SPDX-License-Identifier: GPL-3.0-or-later
from django.contrib import admin
from django.contrib.auth.admin import UserAdmin

from .models import User, Token


class AccountUserAdmin(UserAdmin):
    pass


class TokenAdmin(admin.ModelAdmin):
    list_display = ('created', 'user', 'comment')


admin.site.register(Token, TokenAdmin)
admin.site.register(User, AccountUserAdmin)
