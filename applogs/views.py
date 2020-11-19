import json

from django.http import HttpResponse
from django.views.generic import View

from .models import ClientRecord


class CreateView(View):

    def post(self, request):
        message = request.body.decode('utf-8')
        user_agent = request.META['HTTP_USER_AGENT']
        username = str(request.user)
        headers = None
        if request.headers:
            headers = json.dumps(dict(request.headers))

        record = ClientRecord(message=message, user_agent=user_agent, username=username, headers=headers)
        record.save()

        return HttpResponse('ok')
