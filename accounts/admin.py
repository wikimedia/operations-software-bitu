# SPDX-License-Identifier: GPL-3.0-or-later
from django.contrib import admin
from django.contrib.auth.admin import UserAdmin

from .models import User


class AccountUserAdmin(UserAdmin):
    pass


admin.site.register(User, AccountUserAdmin)
