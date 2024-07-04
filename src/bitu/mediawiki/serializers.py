from rest_framework import serializers

from .models import UserTokenValidation


class UserTokenValidationSerializer(serializers.Serializer):
    username = serializers.CharField(required=True)
    token = serializers.CharField(required=True, write_only=True)
    sul = serializers.CharField(read_only=True)
    valid = serializers.BooleanField(read_only=True)
    enabled = serializers.BooleanField(read_only=True)

    def create(self, validated_data):
        return UserTokenValidation(**validated_data)

    class Meta:
        model = UserTokenValidation
