from django import template

register = template.Library()


@register.simple_tag
def query_string(request, **kwargs):
    income = request.GET.copy()
    for key, value in kwargs.items():
        if value is not None and value != "":
            income[key] = str(value)
        else:
            income.pop(key, None)
    return income.urlencode()
