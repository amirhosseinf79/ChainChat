from django.core.exceptions import ValidationError
from django.http import Http404
from rest_framework import status
from rest_framework.response import Response

from main.api.genericViews.auth import AuthRequiredView
from main.api.serializers.allMessages import MessageSerializer, PhotoSerializer, VideoSerializer
from main.models import Message, Photo, Video


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
            "details": ["Message id is not correct."],
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
        reply_id = raw_data.pop("reply_id", None)
        self.decide_model(request)
        self.request = request

        if msg_type == "message":
            self.default_serializer = MessageSerializer

        elif msg_type == "photo":
            self.default_serializer = PhotoSerializer

        elif msg_type == "video":
            self.default_serializer = VideoSerializer

        if self.message_id:
            try:
                self.instance_obj = self.default_model.objects.get(pk=self.message_id)
            except self.default_model.DoesNotExist:
                raise Http404

        if reply_id:
            try:
                instance_obj = self.default_model.objects.get(pk=reply_id)
                try:
                    raw_data["reply_id"] = instance_obj.message_controller.id
                except Exception as e:
                    try:
                        print(e)
                        raw_data["reply_id"] = instance_obj.video_controller.id
                    except Exception as e:
                        print(e)
                        raw_data["reply_id"] = instance_obj.photo_controller.id

            except self.default_model.DoesNotExist:
                pass

        if self.default_serializer:
            self.default_serializer_class = self.default_serializer(
                instance=self.instance_obj, data=raw_data, context={'user': self.request.user})

    def handle_serializer_response(self):
        if not self.default_serializer_class:
            return self.message_type_incorrect()

        if self.default_serializer_class.is_valid():
            self.default_serializer_class.save()
            return Response(self.default_serializer_class.data, status=status.HTTP_200_OK)
        else:
            return Response(self.default_serializer_class.errors, status=status.HTTP_400_BAD_REQUEST)

    def handle_model_response(self, pk, raw_data, func, st):
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