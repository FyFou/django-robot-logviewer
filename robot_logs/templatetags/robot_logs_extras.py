from django import template

register = template.Library()

@register.filter
def get_item(dictionary, key):
    """Renvoie la valeur correspondant à une clé donnée dans un dictionnaire"""
    return dictionary.get(key, '')
