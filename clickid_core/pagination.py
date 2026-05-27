"""
Paginação customizada para permitir page_size maior
"""
from rest_framework.pagination import PageNumberPagination


class LargeResultsSetPagination(PageNumberPagination):
    """
    Paginação que permite buscar até 10.000 registros por página
    """
    page_size = 100  # Padrão
    page_size_query_param = 'page_size'  # Permite ?page_size=X
    max_page_size = 10000  # Máximo permitido
