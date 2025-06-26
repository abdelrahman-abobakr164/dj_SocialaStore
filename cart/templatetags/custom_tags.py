from django import template
import json

register = template.Library()


@register.filter
def jsonify(dictionary):
    return json.dumps(dictionary)


@register.filter
def get_item(dictionary, key):
    return dictionary.get(str(key), 0)
