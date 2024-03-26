from rest_framework import serializers

from .models import UserValidation, username_validators, uid_validators


class UserValidationSerializer(serializers.Serializer):
    username = serializers.CharField(validators=username_validators)
    uid = serializers.CharField(required=False, validators=uid_validators)
    sanitized = serializers.CharField(read_only=True)

    def create(self, validated_data):
        return UserValidation(**validated_data)

    class Meta:
        model = UserValidation
