from rest_framework import serializers

from bitu.helpers import list_backends
from .models import SecurityToken, User

from keymanagement.serializers import SSHKeySerializer


class SecurityTokenValidationSerializer(serializers.Serializer):
    user = serializers.CharField(required=True)
    token = serializers.CharField(required=True, write_only=True)
    valid = serializers.SerializerMethodField(read_only=True, default=False)
    enabled = serializers.SerializerMethodField(read_only=True, default=False)

    _security_token = None

    def _get_security_token(self, attrs):
        if self._security_token:
            return self._security_token

        try:
            self._security_token = SecurityToken.objects.get(user__username=attrs['user'], enabled=True)
        except SecurityToken.DoesNotExist:
            return None
        return self._security_token

    def get_valid(self, attrs):
        return self._get_security_token(attrs).validate(attrs['token']) if self._get_security_token(attrs) else False

    def get_enabled(self, attrs):
        return self._get_security_token(attrs).enabled if self._get_security_token(attrs) else False

    class Meta:
        model = SecurityToken
        fields = ['user', 'valid', 'enabled']


class UserSerializer(serializers.Serializer):
    id = serializers.IntegerField()
    username = serializers.CharField()
    email = serializers.CharField()
    ssh_keys = SSHKeySerializer(many=True, read_only=True)
    backends = serializers.SerializerMethodField()

    def get_backends(self, obj):
        return list_backends(manage_ssh_keys=True)

    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'ssh_keys', 'backends']