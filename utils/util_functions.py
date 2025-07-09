from functools import wraps
from django.core.exceptions import PermissionDenied
from django.utils import timezone


def admin_required():
    def decorator(view_func):
        @wraps(view_func)
        def _wrapped_view(request, *args, **kwargs):
            user = request.user
            if user.is_authenticated and user.is_admin:
                return view_func(request, *args, **kwargs)
            raise PermissionDenied
        return _wrapped_view
    return decorator

def format_phone(phone):
    if not phone:
        return "N/A"
    if len(phone) >= 13:
        return f"{phone[:4]} {phone[4:7]} {phone[7:10]} {phone[10:]}"
    return phone

def conv_timezone(dt, dt_format):
    dtime = timezone.localtime(dt)
    return dtime.strftime(dt_format)