from django.core.exceptions import ObjectDoesNotExist
from django.http import Http404
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from main.api.genericViews.auth import AuthRequiredView
from main.api.genericViews.chatAndGroup import ChatViewBase, CreateBaseView
from main.api.genericViews.messagesView import ManageMessageBase
from main.api.genericViews.userVeiw import UserBaseView
from main.api.serializers.chatMembers import ChatMemberSerializer
from main.api.serializers.users import AuthUserSerializer
from main.models import Chat, MessageController
from main.api.serializers.allMessages import (AllMessageSerializer,
                                              ChatSerializer,
                                              GroupSerializer)

class GetMyInfo(AuthRequiredView):
    def get(self, request):
        return Response(AuthUserSerializer(request.user).data)


# Create your views here.
class CreateGroup(CreateBaseView):
    serializer_class = GroupSerializer


class ChatCreateView(CreateBaseView):
    serializer_class = ChatSerializer

class ChatListView(ChatViewBase):
    permission_classes = (IsAuthenticated,)
    def get(self, request):
        chats = self.get_query_list(request)
        serializer = ChatSerializer(chats, many=True, context={'user': request.user})
        return self.response(serializer.data)


class ChatDetailsView(ChatViewBase):
    permission_classes = (IsAuthenticated,)
    def get(self, request, pk):
        chat = self.get_query(request, pk)
        serializer = ChatSerializer(chat, context={'user': request.user})
        return Response(serializer.data)

    def delete(self, request, pk):
        chat = self.get_query(request, pk)
        result = chat.delete_chat(request.user)
        return Response(status=status.HTTP_204_NO_CONTENT if result else status.HTTP_403_FORBIDDEN)


class JoinChatView(ChatViewBase):
    def post(self, request):
        group_url = request.data.get('group_url', None)
        try:
            chat = Chat.filtered_objects.get(group__invite_link=group_url)
        except Chat.DoesNotExist:
            raise Http404

        success, result = chat.join_chat(request.user)

        self.base_data.update({
            "success": success,
            "details": result,
        })

        st = status.HTTP_200_OK if success else status.HTTP_400_BAD_REQUEST
        return Response(self.base_data, status=st)


class LeaveChatView(ChatViewBase):
    def post(self, request, pk):
        chat = self.get_query(request, pk, delete_mat=False)
        success, result = chat.leave_chat(request.user)

        self.base_data.update({
            "success": success,
            "details": result,
        })

        st = status.HTTP_200_OK if success else status.HTTP_400_BAD_REQUEST
        return Response(self.base_data, status=st)


class ChatMessagesView(ChatViewBase):
    def get(self, request, pk):
        chat = self.get_query(request, pk)
        content_query = request.GET.get("content", "")
        date_filter = {
            "from_date": request.GET.get("from_date", None),
            "to_date": request.GET.get("to_date", None),
        }
        messages = chat.get_messages(request.user, content_query, date_filter)
        paginated_messages = self.pagination_class.paginate_queryset(messages, request)
        serializer = AllMessageSerializer(paginated_messages, many=True, context={'user': request.user})
        return self.response(serializer.data)


class ChatMembersView(ChatViewBase):
    def get(self, request, pk):
        chat_obj = self.get_query(request, pk)
        user_query = request.GET.get("user", "")
        members = chat_obj.get_members(user_query)
        if members.count() > 0:
            paginated_members = self.pagination_class.paginate_queryset(members, request)
            serializer = ChatMemberSerializer(paginated_members, many=True, context={'user': request.user})
            return self.response(serializer.data)
        else:
            raise Http404


class CreateEditMessageView(ManageMessageBase):
    def post(self, request, pk):
        raw_data = request.data.copy()
        raw_data.update({"author_id": request.user.id, "chat_id": pk})
        message_id = raw_data.get("message_id", -1)
        if message_id > 0:
            self.get_message_id(raw_data)
        self.decide_serializer(request, raw_data)
        return self.handle_serializer_response()


class MessageReadView(ManageMessageBase):
    def post(self, request, pk):
        self.decide_model(request)
        if not self.default_model:
            return self.message_type_incorrect()

        self.get_message_id(request.data)

        if self.message_id > 0:
            try:
                model_obj = self.default_model.filtered_objects.get(id=self.message_id)
                try:
                    self.message_id = model_obj.message_controller.id
                except AttributeError:
                    try:
                        self.message_id = model_obj.video_controller.id
                    except AttributeError:
                        self.message_id = model_obj.photo_controller.id
            except ObjectDoesNotExist:
                return self.message_id_not_found()
        else:
            return self.message_id_not_found()

        raw_data = request.data.copy()
        raw_data.update({"user_id": request.user.id})

        return self.handle_model_response(pk, raw_data, MessageController.objects.mark_seen, status.HTTP_200_OK)


class DeleteMessageView(ManageMessageBase):
    def post(self, request, pk):
        self.decide_model(request)
        if not self.default_model:
            return self.message_type_incorrect()
        return self.handle_model_response(pk, request, self.default_model.filtered_objects.delete_message,
                                          status.HTTP_204_NO_CONTENT)

class GetUsersListView(UserBaseView):
    def get(self, request):
        data = self.get_query_list(request)
        return self.paginator_class.get_paginated_response(data)


class GetUserDetailsView(UserBaseView):
    def get(self, request, pk):
        obj = self.get_query(pk)
        return Response(self.serializer_class(obj, context={"user": request.user}).data)


class BlockUserView(UserBaseView):
    def post(self, request, pk):
        selected_user = self.get_query(pk)
        selected_user.profile.block(request.user.id)
        selected_user = self.get_query(pk)
        serializer = self.serializer_class(selected_user, context={"user": request.user})
        return Response(serializer.data)

class UnblockUserView(UserBaseView):
    def post(self, request, pk):
        selected_user = self.get_query(pk)
        selected_user.profile.unblock(request.user.id)
        selected_user = self.get_query(pk)
        serializer = self.serializer_class(selected_user, context={"user": request.user})
        return Response(serializer.data)



