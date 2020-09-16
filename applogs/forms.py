import json

from django import forms
from django.forms.fields import InvalidJSONInput

from .models import ServerRecord


class JSONFormattedField(forms.JSONField):
    def prepare_value(self, value):
        if isinstance(value, InvalidJSONInput):
            return value
        return json.dumps(value, ensure_ascii=False, indent='  ')


class ServerRecordForm(forms.ModelForm):

    class Meta:
        model = ServerRecord
        fields = [
            'headquater',
            'level',
            'source',
            'method',
            'duration',
            'tags',
            'message',
            'params',
        ]

        field_classes = {
            'params': JSONFormattedField,
        }
        widgets = {
            'params': forms.Textarea(
                attrs={'class': 'acefyelable-textarea', 'data-mode': 'json'}),
        }

    class Media:
        js = ('admin/js/ace/ace.js', 'admin/js/acefy-textarea.js')
