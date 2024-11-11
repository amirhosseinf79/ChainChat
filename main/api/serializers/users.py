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
                "is_blocked": instance.profile.is_blocked(user.id),
            })
        return data


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ("id", "username", "first_name", "last_name", )


class CreateUserSerializer(serializers.ModelSerializer):
    phone_number = serializers.CharField(max_length=10, required=False)
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
