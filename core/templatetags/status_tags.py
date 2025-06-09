# core/templatetags/status_tags.py
from django import template

register = template.Library()

@register.filter
def status_badge_class(status):
    status = status.lower()
    if 'atrasada' in status:
        return 'danger'
    elif 'pendente hoje' in status:
        return 'warning'
    elif 'próxima' in status or 'em dia' in status:
        return 'success'
    elif 'agendada' in status:
        return 'primary'
    elif 'inativa' in status:
        return 'secondary'
    elif '1º agendamento' in status:
        return 'info'
    else:
        return 'light'
