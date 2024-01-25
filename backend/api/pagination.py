from rest_framework.pagination import PageNumberPagination


class LimitPagination(PageNumberPagination):
    page_size_query_param = 'limit'


# class RecipesLimitPagination(PageNumberPagination):
#     page_size = 6
#     page_size_query_param = 'recipes_limit'
#     page_query_param = None
