from django import template
from urllib.parse import urlencode

register = template.Library()

@register.simple_tag
def url_replace(request, field, value):
    """
    Tag personnalisé pour mettre à jour un paramètre d'URL
    sans perdre les autres paramètres existants.
    
    Exemple d'utilisation :
    {% url_replace request 'page' 2 %}
    """
    # Créer une copie du dictionnaire des paramètres
    params = request.GET.copy()
    
    # Mettre à jour ou ajouter le paramètre
    params[field] = value
    
    # Retourner la chaîne de requête encodée
    return params.urlencode()
