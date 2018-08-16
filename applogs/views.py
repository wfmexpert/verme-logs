from .models import ClientRecord
from django.http import HttpResponse
from django.views.generic import View


class CreateView(View):

    def post(self, request):
        message = request.body.decode('utf-8')
        user_agent = request.META['HTTP_USER_AGENT']

        record = ClientRecord(message=message, user_agent=user_agent)
        record.save()

        return HttpResponse('ok')
