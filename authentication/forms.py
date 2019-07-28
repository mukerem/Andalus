from django import forms
from .models import User, Campus, Role, Category, Team
from django.core.validators import RegexValidator
from django.contrib.auth.hashers import check_password
from django.contrib.admin.widgets import FilteredSelectMultiple

class EditMyProfile(forms.ModelForm):
       
    
        
    _campus = forms.CharField(
        widget=forms.TextInput(attrs={'readonly': True}),
    )

    _role = forms.CharField(
        widget=forms.TextInput(attrs={'readonly': True}),
    )

    _category = forms.CharField(
        widget=forms.TextInput(attrs={'readonly': True}),
    )

    _register_date = forms.DateField(
        widget=forms.DateInput(attrs={'readonly': True}),
    )

    _score = forms.DecimalField(
        widget=forms.TextInput(attrs={'readonly': True}),
    )
    class Meta:
        model = User
        fields = ['username', 'first_name', 'last_name', 'phone', 'email', 'sex', 'photo', '_campus', '_role', '_category', '_score', '_register_date']
        # exclude = ['password', 'is_admin', 'last_login','is_active', 'register_date', 'campus', 'category', 'role']
        
    def clean(self):
        cleaned_data = super().clean()
        username = cleaned_data.get('username')
        first_name = cleaned_data.get('first_name')
        last_name = cleaned_data.get('last_name')
        email = cleaned_data.get('email')
        sex = cleaned_data.get('sex')
        if (not username) or (not first_name) or (not last_name) or (not email) or (not sex):
            raise forms.ValidationError("Please correct the errors below.")

        return cleaned_data


class ChangePassword(forms.Form):
    def __init__(self, *args, **kwargs):
        self.password = kwargs.pop('password', None)
        super(ChangePassword, self).__init__(*args, **kwargs)

    old_password = forms.CharField(
        max_length=1024,
        widget=forms.PasswordInput(),
    )
    password_regex = RegexValidator(
        regex=r'^\S{8,1024}',
        message='password must be at least 8 character'
    )
    new_password = forms.CharField(
        label='New password:',
        validators=[password_regex],
        max_length=1024,
        widget=forms.PasswordInput(),
        help_text='minimum 8 character'
    )
    confirm = forms.CharField(
        label='New password confirmation:',
        max_length=1024,
        widget=forms.PasswordInput(),
    )

    def clean(self):
        cleaned_data = super().clean()
        old_password = cleaned_data.get('old_password')
        new_password = cleaned_data.get('new_password')
        confirm_password = cleaned_data.get('confirm')
        if (not old_password) or (not new_password) or (not confirm_password):
            raise forms.ValidationError("Please correct the errors below.")
        # print(check_password(old_password, self.password))

        if check_password(old_password, self.password):
            if new_password:
                if new_password == confirm_password:
                    return
                else:
                    raise forms.ValidationError("password is not confirmed")
        else:
            raise forms.ValidationError("Your old password was entered incorrectly. Please enter it again.")

        return cleaned_data



class SignUp(forms.ModelForm):
    password_regex = RegexValidator(
        regex=r'^\S{8,1024}',
        message='password must be at least 8 character'
    )
    user_password = forms.CharField(
        validators=[password_regex],
        max_length=1024,
        widget=forms.PasswordInput(),
        help_text='*Enter password minimum 8 character',
        label='Password'
    )
    confirm_password = forms.CharField(
        max_length=1024,
        widget=forms.PasswordInput(),
        help_text='*Confirm password'
    )

    class Meta:
        model = User
        fields = ['username', 'first_name', 'last_name', 'phone', 'email', 'sex', 'user_password',
                  'confirm_password',  'photo']
            
        
    def clean(self):
        cleaned_data = super().clean()
        username = cleaned_data.get('username')
        first_name = cleaned_data.get('first_name')
        last_name = cleaned_data.get('last_name')
        user_password = cleaned_data.get('user_password')
        confirm = cleaned_data.get('confirm_password')
        sex = cleaned_data.get('sex')
        email = cleaned_data.get('email')

        if (not username) or (not first_name) or (not last_name) or (not sex) or (not user_password) or (not confirm):
            raise forms.ValidationError("Please correct the errors below.")

        if user_password and confirm:
            if user_password != confirm:
                raise forms.ValidationError("password is not confirmed")
        
        return cleaned_data

    # def clean_confirm_password(self):
    #     user_password = self.cleaned_data.get('password')
    #     confirm = self.cleaned_data.get('confirm_password')

    #     if user_password and confirm:
    #         if user_password != confirm:
    #             raise forms.ValidationError("password is not confirmed")
        
    #     return user_password


class AddUser(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        campus = kwargs.pop('campus', None)

        super(AddUser, self).__init__(*args, **kwargs)
        self.initial['campus'] = campus

    class Meta:
        model = User
        fields = ['username', 'first_name', 'last_name', 'email', 'phone', 'sex', 'role', 'category', 'campus', 'photo']
          
    def clean(self):
        cleaned_data = super().clean()
        username = cleaned_data.get('username')
        first_name = cleaned_data.get('first_name')
        last_name = cleaned_data.get('last_name')
        sex = cleaned_data.get('sex')
        email = cleaned_data.get('email')
        role = cleaned_data.get('role')
        category = cleaned_data.get('category')

        if (not username) or (not first_name) or (not last_name) or (not sex) or (not category) or (not role):
            raise forms.ValidationError("Please correct the errors below.")

        return cleaned_data


class EditUserProfile(forms.ModelForm):

    class Meta:
        model = User
        exclude = ['password', 'is_admin', 'last_login','is_active']
        widgets = {
            'register_date': forms.DateInput(attrs={'readonly': True}),
            'score': forms.TextInput(attrs={'readonly': True}),
        }

    def clean(self):
        cleaned_data = super().clean()
        username = cleaned_data.get('username')
        first_name = cleaned_data.get('first_name')
        last_name = cleaned_data.get('last_name')
        email = cleaned_data.get('email')
        sex = cleaned_data.get('sex')
        role = cleaned_data.get('role')
        category = cleaned_data.get('category')
        if (not username) or (not first_name) or (not last_name) or (not email) or (not sex) or (not role) or (not category):
            raise forms.ValidationError("Please correct the errors below.")

        return cleaned_data

class CSVUserUpload(forms.Form):
    file = forms.FileField(
        label='csv',
        widget=forms.FileInput(),
        help_text='* choose csv file.'

    )




class TeamRegister(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        campus = kwargs.pop('campus', None)

        super(TeamRegister, self).__init__(*args, **kwargs)
        self.initial['campus'] = campus

    class Meta:
        model = Team
        fields = ['username', 'member', 'campus']
            
        widgets = {
            'member': FilteredSelectMultiple(('tags'), is_stacked=True),
        }
        labels = {'username': 'Team name'}
    def clean(self):
        cleaned_data = super().clean()
        name = cleaned_data.get('username')
        member = cleaned_data.get('member')

        if (not name) or (not member):
            raise forms.ValidationError("Please correct the errors below.")
        if member.count() > 3:
            raise forms.ValidationError("Maximum number of user in 1 team is 3.")
        return cleaned_data




class EditTeamProfile(forms.ModelForm):

    class Meta:
        model = Team
        fields = ['username', 'member', 'campus']
            
        widgets = {
            'member': FilteredSelectMultiple(('tags'), is_stacked=True),
        }
        labels={'username': 'Team name'}
    def clean(self):
        cleaned_data = super().clean()
        name = cleaned_data.get('username')
        member = cleaned_data.get('member')

        if (not name) or (not member):
            raise forms.ValidationError("Please correct the errors below.")
        if member.count() > 3:
            raise forms.ValidationError("Maximum number of user in 1 team is 3.")
        return cleaned_data



class GeneratePassword(forms.Form):

    OPTIONS = (
            ("Participant", "Participant"),
            ("Self Registered", "Self Registered"),
            ("Observer", "Observer"),
            ("Organization", "Organization"),
            ("System", "System"),
            )
    category = forms.MultipleChoiceField(widget=forms.CheckboxSelectMultiple,
                                             choices=OPTIONS)
    def clean(self):
        cleaned_data = super().clean()
        category = cleaned_data.get('category')
        if  not category:
            raise forms.ValidationError("Please correct the errors below.")
        return cleaned_data
