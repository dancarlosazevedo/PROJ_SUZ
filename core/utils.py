from django.http import HttpResponseForbidden

def group_required(*group_names):
    def decorator(view_func):
        def _wrapped_view(request, *args, **kwargs):
            if not request.user.is_authenticated:
                return HttpResponseForbidden("Você precisa estar logado.")
            if not request.user.groups.filter(name__in=group_names).exists():
                return HttpResponseForbidden("Você não tem permissão para acessar esta funcionalidade.")
            return view_func(request, *args, **kwargs)
        return _wrapped_view
    return decorator
