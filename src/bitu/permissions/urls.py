from django.contrib.auth.decorators import login_required
from django.urls import path

from .views import (
    MyPermissionView,
    PermissionRequestDetails,
    PermissionRequestView,
    PermissionRequestList,
    PermissionRequestApprove,
)

app_name = 'permissions'
urlpatterns = [
    path('', login_required(MyPermissionView.as_view()), name='list'),
    path('pending/', login_required(PermissionRequestList.as_view()), name='pending'),
    path('approve/<uuid:pk>', login_required(PermissionRequestApprove.as_view()), name='approve'),
    path('log/<uuid:pk>', login_required(PermissionRequestDetails.as_view()), name='log'),
    path('request/<str:system>/<str:key>', login_required(PermissionRequestView.as_view()), name='request'),
]
