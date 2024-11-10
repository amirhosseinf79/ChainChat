from django.core.exceptions import ValidationError
from django.db.models import Q
from django.http import Http404
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from main.api.paginations.custom import CustomPagination
from main.api.serializers.allMessages import AllMessageSerializer, ChatSerializer
from main.api.serializers.chatMembers import ChatMemberSerializer
from main.models import Chat, Group, Message, Photo, Video


class AuthRequiredView(APIView):
    permission_classes = (IsAuthenticated,)


class ChatViewBase(AuthRequiredView):
    pagination_class = CustomPagination()

    def get_query_list(self, request, delete_mat=True):
        title = request.GET.get("title", "")
        not_deleted = Q(members__is_deleted=False) if delete_mat else Q()
        chats = Chat.filtered_objects.find_chat(title).filter(not_deleted, members__member=request.user).distinct()
        paginated_obj = self.pagination_class.paginate_queryset(chats, request)
        return paginated_obj

    def get_query(self, request, pk, delete_mat=True):
        try:
            not_deleted = Q(members__is_deleted=False) if delete_mat else Q()
            chats = Chat.filtered_objects.get(not_deleted, id=pk, members__member=request.user)
        except Chat.DoesNotExist:
            raise Http404

        return chats

    def Response(self, data):
        return self.pagination_class.get_paginated_response(data)


# Create your views here.
class CreateGroup(AuthRequiredView):
    def post(self, request):
        try:
            request.data.update({"user": request.user})
            obj = Group.objects.create_group(**request.data)
            data = {
                "success": True,
                "id": obj.id,
            }
            return Response(data, status=status.HTTP_201_CREATED)
        except TypeError:
            data = {
                "details": "Got unexpected key!"
            }
            return Response(data, status=status.HTTP_400_BAD_REQUEST)
        except ValidationError:
            data = {
                "details": "Got unexpected key!"
            }
            return Response(data, status=status.HTTP_400_BAD_REQUEST)

class ChatCreateView(AuthRequiredView):
    def post(self, request):
        raw_data = request.data
        raw_data.update({"me": request.user.id})
        try:
            obj = Chat.objects.create_private_chat(**raw_data)
        except TypeError:
            obj = None

        except ValidationError:
            obj = None

        if obj:
            data = {
                "success": True,
                "id": obj.id,
            }
            return Response(data, status=status.HTTP_201_CREATED)
        else:
            data = {
                "details": "Got unexpected or incorrect value!"
            }
            return Response(data, status=status.HTTP_400_BAD_REQUEST)

class ChatListView(ChatViewBase):
    permission_classes = (IsAuthenticated,)
    def get(self, request):
        chats = self.get_query_list(request)
        serializer = ChatSerializer(chats, many=True, context={'user': request.user})
        return self.Response(serializer.data)


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
    def post(self, request, pk):
        chat = self.get_query(request, pk, delete_mat=False)
        success, result = chat.join_chat(request.user)

        data = {
            "success": success,
            "details": result,
        }

        if success:
            return Response(data, status=status.HTTP_200_OK)
        else:
            return Response(data, status=status.HTTP_400_BAD_REQUEST)


class LeaveChatView(ChatViewBase):
    def post(self, request, pk):
        chat = self.get_query(request, pk, delete_mat=False)
        success, result = chat.leave_chat(request.user)

        data = {
            "success": success,
            "details": result,
        }

        if success:
            return Response(data, status=status.HTTP_200_OK)
        else:
            return Response(data, status=status.HTTP_400_BAD_REQUEST)


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
        return self.Response(serializer.data)


class ChatMembersView(ChatViewBase):
    def get(self, request, pk):
        chat_obj = self.get_query(request, pk)
        user_query = request.GET.get("user", "")
        members = chat_obj.get_members(user_query)
        if members.count() > 0:
            paginated_members = self.pagination_class.paginate_queryset(members, request)
            serializer = ChatMemberSerializer(paginated_members, many=True, context={'user': request.user})
            return self.Response(serializer.data)
        else:
            raise Http404


class ManageMessageBase(AuthRequiredView):
    def decide_model(self, request):
        msg_type = request.data.pop("message_type", None)

        if msg_type == "message":
            default_model = Message
        elif msg_type == "photo":
            default_model = Photo
        elif msg_type == "video":
            default_model = Video
        else:
            default_model = Message

        return default_model

    def handle_response(self, raw_data, func, status_code):
        data = {}
        try:
            obj = func(**raw_data)
            data.update({"success": True})
            if obj:
                data.update({"id": obj.id})
            st = status_code
        except TypeError:
            data.update({"success": False, "details": "Unexpected value!"})
            st = status.HTTP_400_BAD_REQUEST

        except ValidationError:
            data.update({"success": False, "details": "Got wrong value!"})
            st = status.HTTP_400_BAD_REQUEST

        return Response(data, status=st)

    def create_model(self, request, pk, create_func):
        raw_data = request.data
        raw_data.update({"author": request.user, "chat_id": pk})
        return  self.handle_response(raw_data, create_func, status.HTTP_201_CREATED)

    def update_model(self, request, pk, update_func):
        raw_data = request.data
        raw_data.update({"author": request.user, "chat_id": pk})
        return self.handle_response(raw_data, update_func, status.HTTP_200_OK)

    def delete_model(self, request, pk, delete_func):
        raw_data = request.data
        raw_data.update({"author": request.user, "chat_id": pk})
        return self.handle_response(raw_data, delete_func, status.HTTP_204_NO_CONTENT)


class CreateMessageView(ManageMessageBase):
    def post(self, request, pk):
        default_model = self.decide_model(request)
        return self.create_model(request, pk, default_model.filtered_objects.create_message)

class EditMessageView(ManageMessageBase):
    def put(self, request, pk):
        default_model = self.decide_model(request)
        return self.update_model(request, pk, default_model.filtered_objects.edit_message)

class MessageReadView(ManageMessageBase):
    def post(self, request, pk):
        default_model = self.decide_model(request)
        return self.update_model(request, pk, default_model.filtered_objects.mark_seen)

class DeleteMessageView(ManageMessageBase):
    def post(self, request, pk):
        default_model = self.decide_model(request)
        return self.delete_model(request, pk, default_model.filtered_objects.delete_message)
