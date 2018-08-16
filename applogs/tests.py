from .models import ClientRecord
from django.test import Client, TestCase
from django.urls import reverse


class ClientCreateTests(TestCase):
    def post(self, data):
        c = Client(HTTP_USER_AGENT='Chrome IE as Firefox WebKit')
        return c.post(reverse('create'), data, content_type="text/plain")

    def test_ok(self):
        res = self.post('some error')
        self.assertEqual(res.content.decode('utf-8'), 'ok')
        logs = ClientRecord.objects.all()
        self.assertEqual(len(logs), 1, 'should add one log record')
        self.assertEqual(logs[0].message, 'some error')
        self.assertEqual(logs[0].user_agent, 'Chrome IE as Firefox WebKit')
