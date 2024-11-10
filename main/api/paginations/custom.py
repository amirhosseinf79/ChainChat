from rest_framework import pagination
from rest_framework.response import Response


class CustomPagination(pagination.LimitOffsetPagination):
    default_limit = 10

    def get_paginated_response(self, data):
        raw_data = {
            'total': self.count,
            'offset': self.offset,
            'limit': self.limit,
            'results': data
        }
        return Response(raw_data)