import json
from django import forms
from django.contrib.postgres.forms.jsonb import JSONField

from .models import ExportTemplate

try:
    from django.contrib.postgres.forms.jsonb import InvalidJSONInput
except ImportError:
    from django.forms.fields import InvalidJSONInput


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


class ImportTemplateForm(forms.Form):

    class CustomModelChoiceField(forms.ModelChoiceField):
        def label_from_instance(self, obj):
            return f'{obj.name}'

    template = CustomModelChoiceField(queryset=ExportTemplate.objects.all(), widget=forms.Select, required=True)
    file = forms.FileField(required=True)

    def clean_template(self):
        template = self.cleaned_data.get('template')
        if not template:
            raise forms.ValidationError('Выберите шаблон для импорта.')
        return template

    def clean_file(self):
        file = self.cleaned_data.get('file')
        if not file:
            raise forms.ValidationError('Выберите файл для загрузки.')
        return file
