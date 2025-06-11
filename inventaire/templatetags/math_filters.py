from django import template
from django.template.defaultfilters import stringfilter
from django.utils.safestring import mark_safe

register = template.Library()

@register.filter(name='div')
def div(value, arg):
    """
    Divise la valeur par l'argument. Retourne une chaîne vide si la division est impossible.
    """
    try:
        return float(value) / float(arg)
    except (ValueError, ZeroDivisionError, TypeError):
        try:
            return float('nan')
        except (ValueError, TypeError):
            return ''

@register.filter(name='mul')
def mul(value, arg):
    """
    Multiplie la valeur par l'argument.
    """
    try:
        return float(value) * float(arg)
    except (ValueError, TypeError):
        try:
            return float('nan')
        except (ValueError, TypeError):
            return ''

@register.filter(name='sub')
def sub(value, arg):
    """
    Soustrait l'argument de la valeur.
    """
    try:
        return float(value) - float(arg)
    except (ValueError, TypeError):
        try:
            return float('nan')
        except (ValueError, TypeError):
            return ''
