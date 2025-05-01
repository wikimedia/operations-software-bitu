from django.http import HttpResponseForbidden
from rest_framework import generics

from .models import PermissionRequest
from .serializers import PermissionRequestSerializer


class PermissionRequestAPIView(generics.CreateAPIView, generics.RetrieveAPIView):
    queryset = PermissionRequest
    serializer_class = PermissionRequestSerializer

    def get_queryset(self):
        return self.request.user.permission_requests

    def create(self, request, *args, **kwargs):
        if not request.data['user'] == request.user.pk:
            return HttpResponseForbidden("You do not have permission to this object.")
        return super().create(request, *args, **kwargs)
