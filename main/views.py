from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from django.db.models import Q
from django.http import Http404
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from main.api.paginations.custom import CustomPagination
from main.api.serializers.allMessages import AllMessageSerializer, ChatSerializer, GroupSerializer, MessageSerializer, \
    PhotoSerializer, VideoSerializer
from main.api.serializers.chatMembers import ChatMemberSerializer
from main.api.serializers.users import UserMoreInfoSerializer
from main.models import Chat, Message, Photo, Video, MessageController


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
        raw_data = request.data.copy()
        raw_data.update({"user": request.user.id})
        serializer = self.serializer_class(data=raw_data)

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
    default_serializer = None
    default_serializer_class = None
    default_model = None
    instance_obj = None
    message_id = None
    request = None

    def message_type_incorrect(self):
        self.base_data.update({
            "details": ["message type is incorrect."],
        })
        return Response(self.base_data, status=status.HTTP_400_BAD_REQUEST)

    def message_id_not_found(self):
        self.base_data.update({
            "details": ["Message id is not provided."],
        })
        return Response(self.base_data, status=status.HTTP_400_BAD_REQUEST)

    def get_message_id(self, request):
        self.message_id = request.get("message_id", -1)
        return self.message_id

    def decide_model(self, request):
        raw_data = request.data.copy()
        msg_type = raw_data.pop("type", None)
        self.request = request

        if msg_type == "message":
            self.default_model = Message
        elif msg_type == "photo":
            self.default_model = Photo
        elif msg_type == "video":
            self.default_model = Video

    def decide_serializer(self, request, raw_data):
        msg_type = raw_data.pop("type", None)
        self.request = request

        if msg_type == "message":
            self.default_serializer = MessageSerializer
            if self.message_id:
                try:
                    self.instance_obj = Message.objects.get(pk=self.message_id)
                except Message.DoesNotExist:
                    raise Http404

        elif msg_type == "photo":
            self.default_serializer = PhotoSerializer
            if self.message_id:
                try:
                    self.instance_obj = Photo.objects.get(pk=self.message_id)
                except Photo.DoesNotExist:
                    raise Http404

        elif msg_type == "video":
            self.default_serializer = VideoSerializer
            if self.message_id:
                try:
                    self.instance_obj = Video.objects.get(pk=self.message_id)
                except Video.DoesNotExist:
                    raise Http404

        if self.default_serializer:
            self.default_serializer_class = self.default_serializer(instance=self.instance_obj, data=raw_data)

    def handle_serializer_response(self):
        if not self.default_serializer_class:
            return self.message_type_incorrect()

        if self.default_serializer_class.is_valid():
            self.default_serializer_class.save()
            return Response(self.default_serializer_class.data, status=status.HTTP_200_OK)
        else:
            return Response(self.default_serializer_class.errors, status=status.HTTP_400_BAD_REQUEST)

    def handle_model_response(self, pk, func, st):
        raw_data = self.request.data.copy()
        raw_data.pop("type", None)
        raw_data.update({"author_id": self.request.user.id, "chat_id": pk})
        raw_data.update({"message_id": self.message_id}) if self.message_id else None

        try:
            func(**raw_data)
        except TypeError:
            st = status.HTTP_400_BAD_REQUEST
            self.base_data.update({
                "details": ["entered values is incorrect."],
            })
        except ValidationError:
            st = status.HTTP_400_BAD_REQUEST
            self.base_data.update({
                "details": ["entered values is incorrect."],
            })

        return Response(self.base_data if self.base_data else None, status=st)


class CreateMessageView(ManageMessageBase):
    def post(self, request, pk):
        raw_data = request.data.copy()
        raw_data.update({"author_id": request.user.id, "chat_id": pk})
        self.decide_serializer(request, raw_data)
        return self.handle_serializer_response()

class EditMessageView(ManageMessageBase):
    def put(self, request, pk):
        raw_data = request.data.copy()
        raw_data.update({"author_id": request.user.id, "chat_id": pk})
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
            self.message_id = self.default_model.objects.get(id=self.message_id).message_controller.id
        else:
            return self.message_id_not_found()

        return self.handle_model_response(pk, MessageController.objects.mark_seen, status.HTTP_200_OK)


class DeleteMessageView(ManageMessageBase):
    def post(self, request, pk):
        self.decide_model(request)
        if not self.default_model:
            return self.message_type_incorrect()
        return self.handle_model_response(pk, self.default_model.filtered_objects.delete_message,
                                          status.HTTP_204_NO_CONTENT)


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



