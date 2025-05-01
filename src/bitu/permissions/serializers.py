from django.contrib.auth import get_user_model
from django.utils.translation import gettext_lazy as _

from rest_framework import serializers
from .models import Log, PermissionRequest


User = get_user_model()


class PermissionLogSerializer(serializers.ModelSerializer):
    username = serializers.SerializerMethodField()

    def get_username(self, obj):
        return obj.created_by.get_username()

    class Meta:
        model = Log
        fields = ['created', 'approved', 'comment', 'username']
        depth = 1


class PermissionRequestSerializer(serializers.ModelSerializer):
    user = serializers.PrimaryKeyRelatedField(required=True, queryset=User.objects.all())
    comment = serializers.CharField(
        allow_blank=False,
        error_messages={'blank': _("Please provide a reason for requesting this permission.")})
    logs = PermissionLogSerializer(source='log_set', many=True, read_only=True)

    def create(self, validated_data):
        return PermissionRequest.objects.create(**validated_data)

    class Meta:
        model = PermissionRequest
        fields = ['user', 'key', 'system', 'comment', 'logs']
        depth = 1
