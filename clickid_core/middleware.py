import time
import logging

logger = logging.getLogger('django')

class RequestLoggingMiddleware:
    """Lightweight middleware to log request start/end with timing.

    Useful for diagnosing whether requests reach Django and how long
    view/middleware processing takes. Safe for production (minimal overhead).
    """
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        start = time.monotonic()
        try:
            remote = request.META.get('REMOTE_ADDR') or request.META.get('HTTP_X_FORWARDED_FOR', '')
            content_length = request.META.get('CONTENT_LENGTH', '-')
            logger.info("request_start: method=%s path=%s remote=%s content_length=%s", request.method, request.get_full_path(), remote, content_length)
        except Exception:
            # Ensure middleware never raises
            logger.exception('request_start: logging failed')

        response = None
        try:
            response = self.get_response(request)
            return response
        finally:
            try:
                duration = time.monotonic() - start
                status = getattr(response, 'status_code', 'N/A')
                logger.info("request_end: method=%s path=%s duration=%.3fs status=%s", request.method, request.get_full_path(), duration, status)
            except Exception:
                logger.exception('request_end: logging failed')
