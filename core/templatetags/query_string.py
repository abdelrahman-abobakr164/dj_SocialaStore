from django import template


register = template.Library()


@register.simple_tag
def query_string(request, **kwargs):
    income = request.GET.copy()
    for key, value in kwargs.items():
        if value is not None:
            income[key] = value
        else:
            income.pop(key, None)
    return income.urlencode()
