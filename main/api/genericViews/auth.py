from rest_framework import status
from rest_framework.authtoken.models import Token
from rest_framework.authtoken.views import ObtainAuthToken
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from main.api.serializers.users import CreateUserSerializer


class AuthLoginView(ObtainAuthToken):
    def post(self, request, *args, **kwargs):
        response = super().post(request, *args, **kwargs)
        token = Token.objects.get(key=response.data['token'])
        # obj = ExpiringToken.objects.create(token=token)
        # token.save()
        return Response({'token': token.key, 'expires': token.options.expiration_date})


class AuthCreateUserView(APIView):
    serializer_class = CreateUserSerializer
    success_msg = "User created successfully."

    def post(self, request):
        user = self.serializer_class(data=request.data)

        if user.is_valid():
            user.save()
            return Response({'message': self.success_msg}, status=status.HTTP_201_CREATED)
        else:
            return Response(user.errors, status=status.HTTP_400_BAD_REQUEST)


class AuthRequiredView(APIView):
    permission_classes = (IsAuthenticated,)
    base_data = {}