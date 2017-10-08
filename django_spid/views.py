
from django.shortcuts import render
from django.template.response import TemplateResponse


def index(req):
    return TemplateResponse(req, 'base/button.html')
