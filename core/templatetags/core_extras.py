from django import template

register = template.Library()

@register.filter
def get_attr(obj, attr_name):
    """Dynamically get an attribute from an object."""
    return getattr(obj, attr_name, False)
