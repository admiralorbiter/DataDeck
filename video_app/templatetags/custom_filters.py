from django import template
from video_app.models import Session

register = template.Library()

@register.filter
def get_session(session_id):
    try:
        return Session.objects.get(id=session_id)
    except Session.DoesNotExist:
        return None
