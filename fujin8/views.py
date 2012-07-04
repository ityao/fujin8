# Create your views here.
from django.shortcuts import render_to_response
from django.template.context import RequestContext
from django.views.decorators.csrf import ensure_csrf_cookie

@ensure_csrf_cookie
def home(request):
    return render_to_response('index.html', locals(), context_instance=RequestContext(request))
