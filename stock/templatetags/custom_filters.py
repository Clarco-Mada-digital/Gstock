from django import template

register = template.Library()

@register.filter
def model_name(obj):
    """
    Renvoie le nom du modèle en minuscules pour un objet donné.
    Exemple d'utilisation dans le template : {{ object|model_name }}
    """
    try:
        return obj._meta.model_name
    except AttributeError:
        return ''

@register.filter
def model_name_verbose(obj):
    """
    Renvoie le nom lisible du modèle pour un objet donné.
    Exemple d'utilisation dans le template : {{ object|model_name_verbose }}
    """
    try:
        return obj._meta.verbose_name
    except AttributeError:
        return ''
