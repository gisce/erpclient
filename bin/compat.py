import sys
import logging


logger = logging.getLogger('common.compat')


if sys.version_info < (2, 7):
    import urllib2

    class HTTPErrorProcessor(urllib2.HTTPErrorProcessor):
        """Process HTTP error responses."""
        handler_order = 1000  # after all other processing

        def http_response(self, request, response):
            code, msg, hdrs = response.code, response.msg, response.info()

            # According to RFC 2616, "2xx" code indicates that the client's
            # request was successfully received, understood, and accepted.
            if not (200 <= code < 300):
                response = self.parent.error(
                    'http', request, response, code, msg, hdrs)

            return response

        https_response = http_response


    logger.info("Install custom opener...")
    opener = urllib2.build_opener(HTTPErrorProcessor)
    urllib2.install_opener(opener)