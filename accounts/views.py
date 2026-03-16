from django.shortcuts import render
from django.http import HttpResponse


def index(request):
    return HttpResponse("Accounts app is up")

# Create your views here.
