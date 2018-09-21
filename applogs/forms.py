from django import forms

from .models import ServerRecord
from django.contrib.postgres.forms.jsonb import InvalidJSONInput, JSONField

class JSONFormattedField(JSONField):
    def prepare_value(self, value):
        if isinstance(value, InvalidJSONInput):
            return value
        return json.dumps(value, ensure_ascii=False, indent='  ')
    
class ServerRecordForm(forms.ModelForm):
    class Meta:
        model = ServerRecord
        fields = '__all__'
        field_classes = {
            'params': JSONFormattedField,
        }
        widgets = {
            'params': forms.Textarea(
                attrs={'class': 'acefyelable-textarea', 'data-mode': 'json'}),
        }

    class Media:
        js = ('admin/js/ace/ace.js', 'admin/js/acefy-textarea.js')
