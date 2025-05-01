from rest_framework.permissions import DjangoModelPermissions
from rest_framework import generics, status
from rest_framework.response import Response
from .models import SecurityToken
from .serializers import SecurityTokenValidationSerializer, UserSerializer, SSHKeySerializer

from django.http import HttpResponseForbidden

class SecurityTokenValidationAPI(generics.GenericAPIView):
    permission_classes = [DjangoModelPermissions]
    queryset = SecurityToken.objects.filter(enabled=True)
    lookup_field = 'user'
    serializer_class = SecurityTokenValidationSerializer

    def post(self, request):
        serializer = self.serializer_class(data=request.data)
        if serializer.is_valid():
            return Response(serializer.data,
                            status=status.HTTP_200_OK)
        return Response(serializer.errors,
                        status=status.HTTP_400_BAD_REQUEST)


class UserAPI(generics.RetrieveAPIView):
    serializer_class = UserSerializer

    def get_object(self):
        return self.request.user


class CreateSSHKey(generics.CreateAPIView, generics.DestroyAPIView, generics.UpdateAPIView):
    queryset = SSHKeySerializer.Meta.model
    serializer_class = SSHKeySerializer

    def get_queryset(self):
        return self.request.user.ssh_keys

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        if not instance.user == request.user:
            return HttpResponseForbidden("You do not have permission to this object.")

        instance.active = False
        instance.save()
        self.perform_destroy(instance)
        return Response(status=status.HTTP_204_NO_CONTENT)

    def update(self, request, *args, **kwargs):
        if not request.data['user'] == request.user.pk:
            return HttpResponseForbidden("You do not have permission to this object.")
        return super().update(request, *args, **kwargs)

    def create(self, request, *args, **kwargs):
        if not request.data['user'] == request.user.pk:
            return HttpResponseForbidden("You do not have permission to this object.")
        return super().create(request, *args, **kwargs)