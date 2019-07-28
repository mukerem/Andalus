from django import forms
from .models import ClarificationFromAdmin


class SendClarification(forms.Form):

    message = forms.CharField(
        widget=forms.Textarea(),
        label=''
    )
    
    def clean(self):
        cleaned_data = super().clean()
        message = cleaned_data.get('message')
    
        if not message:
            raise forms.ValidationError("Please correct the errors below.")
        return cleaned_data


class AdminClarification(forms.ModelForm):

    class Meta:
        model = ClarificationFromAdmin
        fields = ['message', 'is_public', 'team', 'user']

    def clean(self):
        cleaned_data = super().clean()
        message = cleaned_data.get('message')
        user = cleaned_data.get('user')
        team = cleaned_data.get('team')
        is_public = cleaned_data.get('is_public')
        if not message:
            raise forms.ValidationError("Please correct the errors below.")
        if is_public:
            if user or team:
                raise forms.ValidationError("If is_public is True there is no need of user and team.")
        else:
            if user and team:
                raise forms.ValidationError("Choose either user or team.")

        return cleaned_data
