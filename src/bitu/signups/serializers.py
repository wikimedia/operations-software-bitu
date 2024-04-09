from rest_framework import serializers

from .models import BlockListIP, UserValidation, username_validators, uid_validators


class BlockListIPSerializer(serializers.ModelSerializer):
    network = serializers.ReadOnlyField()

    class Meta:
        model = BlockListIP
        fields = ['comment', 'expiry', 'network']


class UserValidationSerializer(serializers.Serializer):
    username = serializers.CharField(validators=username_validators)
    uid = serializers.CharField(required=False, validators=uid_validators)
    sanitized = serializers.CharField(read_only=True)

    def create(self, validated_data):
        return UserValidation(**validated_data)

    class Meta:
        model = UserValidation
