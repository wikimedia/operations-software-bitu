from django.contrib.auth.decorators import login_required
from django.urls import path

from .views import (
    MyPermissionView,
    PermissionRequestView,
    PermissionRequestDetails,
)

app_name = 'permissions'
urlpatterns = [
    path('', login_required(MyPermissionView.as_view()), name='list'),
    path('log/<uuid:pk>', login_required(PermissionRequestDetails.as_view()), name='log'),
    path('<str:system>/<str:key>', login_required(PermissionRequestView.as_view()), name='request'),
]
