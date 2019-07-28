from django import forms
from .models import Submit


class SubmitAnswer(forms.ModelForm):
    # source_code = forms.CharField(
    #     max_length=100000,
    #     required=False,
    #     widget=forms.Textarea(),
    #     help_text='write the code here'
    # )
    class Meta:
        model = Submit
        fields = ['submit_file', 'problem', 'language']
        
        # labels = {'submit_file': 'Source Code '}
      
    def clean(self):
        cleaned_data = super().clean()
        file = cleaned_data.get('submit_file')
        language = cleaned_data.get('language')
        problem = cleaned_data.get('problem')

        if (not file) or (not problem) or (not language):
            raise forms.ValidationError("Please correct the errors below.")

        return cleaned_data
