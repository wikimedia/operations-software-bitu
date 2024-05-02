from django.core.exceptions import PermissionDenied
from django.views.generic.base import View


class ObjectAccessRestrictMixin(View):
    """Mixin for ensuring that only the users own objects are able to be
    displayed, edited, or deleted by the current user.

    Args:
        View (django.views.generic.base.View): django base view
    """

    def get_queryset(self):
        return super().get_queryset().filter(user=self.request.user)

    def dispatch(self, request, *args, **kwargs):
        pk = kwargs.get('pk')

        if not pk:
            return super().dispatch(request, *args, **kwargs)

        try:
            # Fetch object as normal, but add the user to the query.
            self.model.objects.get(pk=pk, user=request.user)
            return super().dispatch(request, *args, **kwargs)
        except self.model.DoesNotExist:
            raise PermissionDenied()
