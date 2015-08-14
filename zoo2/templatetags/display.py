from django import template

from zoo2.models import HTMLBlock

register = template.Library()


@register.inclusion_tag('complete.html')
def complete(counts):
	return {
		'translated': counts[0],
		'translated_width': float(counts[0]) * 100 / counts[3],
		'duplicate': counts[1],
		'duplicate_width': float(counts[1]) * 100 / counts[3],
		'missing': counts[2],
		'missing_width': float(counts[2]) * 100 / counts[3],
		'total': counts[3]
	}


@register.simple_tag
def html_block(alias):
	try:
		return HTMLBlock.objects.get(alias=alias).html
	except HTMLBlock.DoesNotExist:
		return ''
