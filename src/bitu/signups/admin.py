# SPDX-License-Identifier: GPL-3.0-or-later
from django.contrib import admin

from .models import (
    BlockListIP,
    BlockListUsername,
    Signup,
    SignupPassword)


def send_activation_link(modeladmin, request, queryset):
    for signup in queryset:
        signup.send_activation_link()


send_activation_link.short_description = "Resend activation link"


class BlockListIPAdmin(admin.ModelAdmin):
    list_display = ['network', 'start', 'end', 'created_date', 'expiry']


class BlockListUsernameAdmin(admin.ModelAdmin):
    list_display = ['regex', 'comment']
    list_filter = ['origin']
    readonly_fields = ['created_date', 'last_modified']


class SignupAdmin(admin.ModelAdmin):
    list_display = ['username', 'uid', 'email', 'created_date', 'last_modified']
    fields = ['username', 'uid', 'email']
    actions = [send_activation_link]


class SignupAdminPassword(admin.ModelAdmin):
    list_display = ['username', 'email', 'created', 'module']

    def created(self, obj: SignupPassword):
        return obj.signup.created_date

    def email(self, obj: SignupPassword):
        return obj.signup.email

    def username(self, obj: SignupPassword):
        return obj.signup.username


admin.site.register(BlockListIP, BlockListIPAdmin)
admin.site.register(BlockListUsername, BlockListUsernameAdmin)
admin.site.register(Signup, SignupAdmin)
admin.site.register(SignupPassword, SignupAdminPassword)
