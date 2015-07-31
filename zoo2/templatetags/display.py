from django import template

register = template.Library()

@register.inclusion_tag('complete.html')
def complete(counts):
	return {
		'translated': counts[0],
		'duplicate': counts[1],
		'missing': counts[2],
		'total': counts[3]
	}
