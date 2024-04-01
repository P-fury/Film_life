from django import forms
from django.contrib.auth.models import User
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from django.core.exceptions import ValidationError
from django.db import models
from pycparser.ply.yacc import Production

from film_lifeapp.models import ProductionHouse, Contact


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


class ContactDeleteForm(forms.Form):
    action = forms.CharField(validators=[check_button])


class ContactAddForm(forms.ModelForm):
    def __init__(self, user, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['first_name'].widget.attrs.update({
            'placeholder': 'First Name',
            'class': 'center',
        })
        self.fields['last_name'].widget.attrs.update({
            'placeholder': 'Last Name',
            'class': 'center',
        })
        self.fields['occupation'].widget.attrs.update({
            'placeholder': 'Occupation',
            'class': 'center',
        })
        self.fields['email'].widget.attrs.update({
            'placeholder': 'Email',
            'class': 'center',
        })
        self.fields['phone'].widget.attrs.update({
            'placeholder': 'Phone',
            'class': 'center',
        })
        self.fields['notes'].widget.attrs.update({
            'placeholder': 'Notes',
            'class': 'center',
        })

        # Pobierz wszystkie domy produkcyjne użytkownika
        production_houses = ProductionHouse.objects.filter(user=user)
        # Utwórz wybory dla pola production_house
        self.fields['production_house'] = forms.ModelMultipleChoiceField(
            queryset=production_houses,
            widget=forms.CheckboxSelectMultiple(),
            required=False,
        )

    class Meta:
        model = Contact
        fields = ['first_name', 'last_name', 'occupation', 'production_house', 'email', 'phone', 'notes']
        widgets = {
            'production_house': forms.SelectMultiple(attrs={'placeholder': 'Select Production House'})
        }


# ==================== SEARCH FORM ===================

class SearchByDateForm(forms.Form):
    start_date = forms.DateField(label='Start Date', widget=forms.DateInput(attrs={'type': 'date'}))
    end_date = forms.DateField(label='End Date', widget=forms.DateInput(attrs={'type': 'date'}))
