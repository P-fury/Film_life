from django import forms
from django.contrib.auth.models import User
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from django.core.exceptions import ValidationError
from django.db import models
from pycparser.ply.yacc import Production

from film_lifeapp.models import ProductionHouse


class RegisterUserForm(UserCreationForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['username'].widget.attrs.update({
            'placeholder': 'UserName',
            'minlength': '4',
            'maxlength': '24',
        })
        self.fields['password1'].widget.attrs.update({
            'placeholder': 'Password',
            'minlength': '8',
            'maxlength': '64',
        })
        self.fields['password2'].widget.attrs.update({
            'placeholder': 'RePassword',
            'minlength': '8',
            'maxlength': '64',
        })
        self.fields['email'].widget.attrs.update({
            'placeholder': 'Email - not needed to register',
        })
        self.fields['first_name'].widget.attrs.update({
            'placeholder': 'first name - not needed to register',
        })
        self.fields['last_name'].widget.attrs.update({
            'placeholder': 'last name - not needed to register',
        })

    class Meta:
        model = User
        fields = ['username', 'email', 'password1', 'password2', 'first_name', 'last_name']


class LoginForm(AuthenticationForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['username'].widget.attrs.update({
            'placeholder': 'UserName',
            'minlength': '4',
            'maxlength': '24',
        })
        self.fields['password'].widget.attrs.update({
            'placeholder': 'Password',
            'minlength': '8',
            'maxlength': '64',
        })


class EditUserForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ['username', 'email', 'first_name', 'last_name']


class EditProductionForm(forms.ModelForm):
    class Meta:
        model = ProductionHouse
        fields = '__all__'


# =============== DELETE FORMS AND VALIDATORS ===================
def check_button(value):
    if value != 'YES':
        raise ValidationError('')


class ProjectDeleteForm(forms.Form):
    action = forms.CharField(validators=[check_button])


class DaysDeleteForm(forms.Form):
    action = forms.CharField(validators=[check_button])


class ProductionHouseDeleteForm(forms.Form):
    action = forms.CharField(validators=[check_button])
