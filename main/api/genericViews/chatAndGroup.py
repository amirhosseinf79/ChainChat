from django.db.models import Q
from django.http import Http404

from main.api.genericViews.auth import AuthRequiredView
from main.api.paginations.custom import CustomPagination
from main.models import Chat


class ChatViewBase(AuthRequiredView):
    pagination_class = CustomPagination()
    model_class = Chat.filtered_objects

    def get_query_list(self, request, delete_mat=True):
        title = request.GET.get("title", "")
        not_deleted = Q(members__is_deleted=False) if delete_mat else Q()
        chats = self.model_class.find_chat(title).filter(not_deleted, members__member=request.user).distinct()
        paginated_obj = self.pagination_class.paginate_queryset(chats, request)
        return paginated_obj

    def get_query(self, request, pk, delete_mat=True):
        try:
            not_deleted = Q(members__is_deleted=False) & Q(members__member=request.user) if delete_mat else Q()
            chats = self.model_class.get(not_deleted, id=pk)
        except Chat.DoesNotExist:
            raise Http404

        return chats

    def response(self, data):
        return self.pagination_class.get_paginated_response(data)