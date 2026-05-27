from django.db import connections
import logging

logger = logging.getLogger(__name__)

def close_db_connections():
    """Close all DB connections. Use sparingly: helpful during dev after heavy proxy loops.

    This is a pragmatic mitigation for development when internal proxy HTTP calls
    may cause many short-lived DB connections to accumulate. In production prefer
    a connection pooler (pgbouncer) or proper refactor to avoid HTTP proxying.
    """
    try:
        connections.close_all()
        logger.debug('Closed all DB connections via close_db_connections()')
    except Exception as e:
        logger.exception('Error closing DB connections: %s', e)


def get_request_params(request):
    """Return a DRF-like query params mapping.

    If `request` is a DRF `Request` it has `query_params`. If it's a
    plain Django `HttpRequest`/`WSGIRequest`, fall back to `GET`.
    This helper centralizes the fallback behaviour to avoid AttributeError
    when views are called from Django web views that pass a WSGIRequest.
    """
    params = getattr(request, 'query_params', None)
    if params is None:
        return getattr(request, 'GET', {})
    return params
