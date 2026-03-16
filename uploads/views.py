from django.shortcuts import render
from django.http import HttpResponse


def index(request):
    return HttpResponse("Uploads app is running")

# Create your views here.
