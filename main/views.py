from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from django.db.models import Q
from django.http import Http404
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from main.api.paginations.custom import CustomPagination
from main.api.serializers.allMessages import AllMessageSerializer, ChatSerializer, GroupSerializer
from main.api.serializers.chatMembers import ChatMemberSerializer
from main.api.serializers.users import UserMoreInfoSerializer
from main.models import Chat, Message, Photo, Video


class AuthRequiredView(APIView):
    permission_classes = (IsAuthenticated,)
    base_data = {}


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


class CreateBaseView(AuthRequiredView):
    serializer_class = None
    fields = None

    def post(self, request):
        request.data.update({"user": request.user.id})
        serializer = self.serializer_class(data=request.data)

        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        else:
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

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
        try:
            obj = func(**raw_data)
            self.base_data.update({"success": True})
            if obj:
                self.base_data.update({"id": obj.id})
            st = status_code
        except TypeError:
            self.base_data.update({"success": False, "details": "Unexpected value!"})
            st = status.HTTP_400_BAD_REQUEST

        except ValidationError:
            self.base_data.update({"success": False, "details": "Got wrong value!"})
            st = status.HTTP_400_BAD_REQUEST

        return Response(self.base_data, status=st)

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


class UserBaseView(AuthRequiredView):
    paginator_class = CustomPagination()
    serializer_class = UserMoreInfoSerializer
    model_class = User

    def get_query_list(self, request):
        username = request.GET.get("q", "")

        if username or len(username) >= 3:
            obj = self.model_class.objects.filter(username__contains=username)
        else:
            obj = self.model_class.objects.exclude(is_active=True)

        paginated_user = self.paginator_class.paginate_queryset(obj, request)
        serializer = self.serializer_class(paginated_user, many=True, context={"user": request.user})

        return serializer.data

    def get_query(self, pk):
        try:
            obj = self.model_class.objects.get(id=pk)
        except User.DoesNotExist:
            raise Http404

        return obj

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



