from rest_framework.permissions import DjangoModelPermissions
from rest_framework import generics, status
from rest_framework.response import Response
from .models import SecurityToken
from .serializers import SecurityTokenValidationSerializer


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
