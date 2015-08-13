from django.conf import settings


class SecurityMiddleware(object):
    def __init__(self):
        self.sts_seconds = settings.SECURE_HSTS_SECONDS
        self.sts_include_subdomains = settings.SECURE_HSTS_INCLUDE_SUBDOMAINS
        self.content_type_nosniff = settings.SECURE_CONTENT_TYPE_NOSNIFF
        self.xss_filter = settings.SECURE_BROWSER_XSS_FILTER

    def process_request(self, request):
        pass

    def process_response(self, request, response):
        if (self.sts_seconds and
                'strict-transport-security' not in response):
            sts_header = "max-age=%s" % self.sts_seconds

            if self.sts_include_subdomains:
                sts_header = sts_header + "; includeSubDomains"

            response["strict-transport-security"] = sts_header

        if self.content_type_nosniff and 'x-content-type-options' not in response:
            response["x-content-type-options"] = "nosniff"

        if self.xss_filter and 'x-xss-protection' not in response:
            response["x-xss-protection"] = "1; mode=block"

        return response
