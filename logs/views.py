from django.shortcuts import render
from django.http import HttpResponse


def index(request):
    return HttpResponse("Logs app is operational")

# Create your views here.
