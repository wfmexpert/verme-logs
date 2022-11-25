import json
from django import forms
from django.db.models import JSONField

from .models import ServerRecord

try:
    from django.contrib.postgres.forms.jsonb import InvalidJSONInput
except ImportError:
    from django.forms.fields import InvalidJSONInput


class JSONFormattedField(JSONField):
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
            'request',
            'params',
        ]

        field_classes = {
            'params': JSONFormattedField,
        }
        widgets = {
            'message': forms.Textarea(attrs={'rows': 10, 'cols': 60, }),
            'request': forms.Textarea(attrs={'rows': 45, 'cols': 120, }),
            'params': forms.Textarea(
                attrs={'class': 'acefyelable-textarea', 'data-mode': 'json'}),
        }

    class Media:
        js = ('admin/js/ace/ace.js', 'admin/js/acefy-textarea.js')
