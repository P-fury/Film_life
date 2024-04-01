from django import forms
from django.contrib.auth.models import User
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from django.core.exceptions import ValidationError
from django.db import models
from django.utils.safestring import SafeString
from pycparser.ply.yacc import Production

from film_lifeapp.models import ProductionHouse, Contact, Project, WorkDay, just_numb


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


# ================= EDIT USER  ==================
class EditUserForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ['username', 'email', 'first_name', 'last_name']


# ================= EDIT PROJECT ==================
class EditProjectForm(forms.ModelForm):
    daily_rate = forms.IntegerField(min_value=1,
                                    widget=forms.NumberInput(attrs={'step': 1}))

    CHOICES = [
        ('10', '10%'),
        ('15', '15%'),
        ('progresive', 'Progresive'),
    ]

    type_of_overhours = forms.ChoiceField(choices=CHOICES, required=False)

    class Meta:
        model = Project
        fields = ['name', 'daily_rate', 'type_of_overhours', 'occupation', 'notes', 'production_house']

    def __init__(self, *args, **kwargs):
        kwargs.setdefault('label_suffix', '')
        super().__init__(*args, **kwargs)
        self.fields['notes'].required = False
        self.fields['production_house'].required = False

    def clean_occupation(self):
        occupation = self.cleaned_data['occupation']
        if occupation is None:
            return ""
        return occupation


# ================= EDIT WORK DAY ==================
class EditWorkDayForm(forms.ModelForm):
    date = forms.DateField(widget=forms.DateInput(attrs={'type': 'date'}), required=True)
    amount_of_overhours = forms.IntegerField(min_value=0, max_value=99, widget=forms.NumberInput(attrs={'step': 1}))
    CHOICES = [
        ('shooting day', 'shooting day'),
        ('rehersal', 'rehersal'),
        ('transport', 'transport'),
        ('other', 'other')
    ]
    type_of_workday = forms.ChoiceField(choices=CHOICES, required=True)
    percent_of_daily = forms.IntegerField(min_value=0, max_value=100)

    class Meta:
        model = WorkDay
        fields = '__all__'
        exclude = ['project', 'earnings']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['notes'].required = False
        self.fields['percent_of_daily'].required = False
        if 'type_of_workday' in self.initial and '% of daily rate' in self.initial['type_of_workday']:
            percent = just_numb(self.initial['type_of_workday'])
            self.initial['type_of_workday'] = 'other'
            self.fields['percent_of_daily'].widget.attrs['style'] = 'display: block;'
            self.initial['percent_of_daily'] = percent


# ================= EDIT PRODUCTION ==================
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
