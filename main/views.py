from django.contrib.auth.models import User
from django.http import HttpResponse
from django.shortcuts import render

from main.models import Group


# Create your views here.
def test(request):
    Group.objects.create_group(name='test', user=request.user)
    groups = Group.objects.last()

    return HttpResponse(groups)