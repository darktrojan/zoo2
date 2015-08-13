from django import template

from zoo2.models import HTMLBlock

register = template.Library()


@register.inclusion_tag('complete.html')
def complete(counts):
	return {
		'translated': counts[0],
		'duplicate': counts[1],
		'missing': counts[2],
		'total': counts[3]
	}


@register.simple_tag
def html_block(alias):
	try:
		return HTMLBlock.objects.get(alias=alias).html
	except HTMLBlock.DoesNotExist:
		return ''
