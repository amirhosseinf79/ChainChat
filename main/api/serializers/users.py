from django.contrib.auth.models import User
from rest_framework import serializers
from rest_framework.exceptions import ValidationError

from main.models import Profile


class UserMoreInfoSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ("id", "username", "first_name", "last_name")


    def to_representation(self, instance):
        data = super().to_representation(instance)
        user = self.context.get('user', None)
        if user:
            data.update({
                "last_online": instance.profile.last_online,
                "is_online": instance.profile.is_online,
                "is_blocked": instance.profile.is_blocked(user.id),
                "is_blocked_you": instance.profile.blocked_users.filter(user_id=user.id, is_deleted=False).exists(),
            })
        return data


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ("id", "username", "first_name", "last_name", )


class CreateUserSerializer(serializers.ModelSerializer):
    first_name = serializers.CharField(max_length=255, required=True)
    email = serializers.EmailField(required=True)
    phone_number = serializers.CharField(max_length=10, required=True)
    password = serializers.CharField(write_only=True, required=True)

    class Meta:
        model = User
        fields = ("username", "email", "first_name", "last_name", "phone_number", "password", )

    def validate(self, attrs):
        attrs = super().validate(attrs)
        phone_number = attrs.get('phone_number', None)
        number_exists = Profile.objects.filter(phone_number=phone_number).exists()
        if number_exists:
            raise ValidationError({'phone_number': ['Phone number already exists.']})

        return attrs

    def create(self, validated_data):
        phone_number = validated_data.pop("phone_number", None)
        password = validated_data.pop("password", None)

        user = User.objects.create_user(**validated_data)
        user.set_password(password)
        user.save()
        user.profile.phone_number = phone_number
        user.profile.save()

        return user
