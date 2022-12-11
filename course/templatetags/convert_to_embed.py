from django import template
register = template.Library()

@register.simple_tag
def to_embed(value):
  return value.replace('watch?v=', 'embed/')