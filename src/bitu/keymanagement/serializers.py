from django.contrib.auth import get_user_model
from rest_framework import serializers

from bitu.helpers import list_backends

from .models import SSHKey
from .helpers import ssh_key_string_to_object, key_type_from_str
from .validators import ssh_key_validator, ssh_key_usage_validator


User = get_user_model()


class SSHKeySerializer(serializers.Serializer):
    uuid = serializers.UUIDField(source='id', read_only=True)
    user = serializers.PrimaryKeyRelatedField(required=True, queryset=User.objects.all())
    system = serializers.CharField(required=False)
    system_display = serializers.SerializerMethodField(read_only=True)
    type = serializers.CharField(source='key_type', required=False)
    data = serializers.CharField(source='ssh_public_key', required=False, validators=[ssh_key_validator, ssh_key_usage_validator])
    comment = serializers.CharField(read_only=True)

    def validate_data(self, data):
        try:
            obj = key_type_from_str(data)
            key_type_from_str(data)
        except:
            raise serializers.ValidationError("Invalid SSH key")
        return data

    def get_system_display(self, obj):
        backends = list_backends()
        if obj.system in backends:
            return backends[obj.system]
        return obj.system


    def create(self, validated_data):
        key_object = ssh_key_string_to_object(validated_data['ssh_public_key'])
        validated_data['key_type'] = key_type_from_str(validated_data['ssh_public_key'])
        validated_data['key_size'] = key_object.get_bits()

        if 'system' in validated_data and validated_data['system']:
            validated_data['active'] = True
        return SSHKey.objects.create(**validated_data)

    def update(self, instance, validated_data):
        instance.system = validated_data['system']
        instance.active = True
        instance.save()
        return instance


    class Meta:
        model = SSHKey

