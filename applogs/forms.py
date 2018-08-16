from django import forms

from .models import ServerRecord
from apps.lib.forms import JSONFormattedField


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
