import json
from django import forms
from django.contrib.postgres.forms.jsonb import InvalidJSONInput, JSONField

from .models import ExportTemplate


class JSONFormattedField(JSONField):
    def prepare_value(self, value):
        if isinstance(value, InvalidJSONInput):
            return value
        return json.dumps(value, ensure_ascii=False, indent='  ')


class ExportTemplateForm(forms.ModelForm):
    class Meta:
        model = ExportTemplate
        fields = '__all__'
        field_classes = {
            'queryset': JSONFormattedField,
            'params': JSONFormattedField,
        }
        widgets = {
            'queryset': forms.Textarea(
                attrs={'class': 'acefyelable-textarea', 'data-mode': 'json'}),
            'params': forms.Textarea(
                attrs={'class': 'acefyelable-textarea', 'data-mode': 'json'}),
        }

    class Media:
        js = ('admin/js/ace/ace.js', 'admin/js/acefy-textarea.js')
