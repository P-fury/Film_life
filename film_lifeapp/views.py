import math
import os
import tempfile
import uuid
from datetime import datetime, timezone

import pytz
from django.contrib.auth import logout
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.contrib.auth.models import User
from django.contrib.auth.views import LoginView
from django.http import HttpResponseRedirect, HttpResponse
from django.utils import timezone
from django.shortcuts import render, redirect
from django.urls import reverse_lazy
from django.views import View
from django.views.generic import CreateView, UpdateView, DeleteView
from ip2geotools.databases.noncommercial import DbIpCity

from film_lifeapp.forms import RegisterUserForm, LoginForm, EditProductionForm, ProjectDeleteForm, DaysDeleteForm, \
    ProductionHouseDeleteForm, ContactAddForm, ContactDeleteForm, EditProjectForm, EditWorkDayForm, \
    AddProductionHouseForm, AddProjectForm, PDFUploadForm
from film_lifeapp.models import *
from django.db.models import Sum
from django.contrib import messages
from film_lifeapp.functions import create_pdf, find_timezone

# ========= PDF DOCU ====================
from django.http import FileResponse
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from film_lifeapp.utils import get_piechart

# ========= PDF -> iCalendar ====================
import locale
from pdfminer.high_level import extract_text
from PyPDF2 import PdfFileReader
import pytesseract
from pdf2image import convert_from_path , exceptions
from ics import Calendar, Event
import io

# Create your views here.
# ===================================== HOME JOURNEY ================================
# ------------------------------------- HOME PAGE -----------------------------------
"""
MainView showing last edited project with summary of all work days in PieChart(Matplot lib),
and Start/Stop option for adding new work day to last edited project.

#TODO: NEED TO USE SESSION OR COOKIES FOR BETTER TIME COUNTING 
"""


class MainView(View):

    def get(self, request):
        button_select = True
        try:
            last_project = WorkDay.objects.filter(project__user=request.user).order_by('last_updated').last()
            if last_project is not None:
                if last_project.project.user != request.user:
                    last_project = None
        except WorkDay.DoesNotExist and TypeError:
            return render(request, 'index.html')
        if last_project is not None:
            if len(WorkDay.objects.all()) > 0:
                workdays = WorkDay.objects.filter(project_id=last_project.project_id).count()
            else:
                workdays = 0
        else:
            workdays = None
            # MATPLOT ------
        projects = Project.objects.filter(user=request.user).order_by('-total_earnings_for_project')
        earnings = [x.total_earnings_for_project for x in projects]
        projects_names = [x.name for x in projects]
        try:
            chart = get_piechart(earnings, projects_names)
        except RuntimeError:
            chart = None

        return render(request, 'index.html',
                      {'last_project': last_project, 'workdays': workdays, 'button_select': button_select,
                       'chart': chart})

    def post(self, request):
        # --- GEOLOCALIZATRION FOR STARTSTOP TABLE ----
        user_ip = request.META.get('REMOTE_ADDR', None)
        city = DbIpCity.get(user_ip, api_key='free')
        start = datetime.now(find_timezone(city))
        global worktime
        button_select = True
        try:
            last_project = WorkDay.objects.latest('last_updated')
        except WorkDay.DoesNotExist:
            return render(request, 'index.html')
        if request.POST.get('start-bt') == 'start':
            time_diff = str(datetime.now(find_timezone(city)))[-6:]
            worktime = StartStop.objects.create(start_time=start, time_diff=time_diff)
            button_select = False
        if request.POST.get('stop-bt') == 'stop':
            button_select = True
            stop = datetime.now(find_timezone(city))
            worktime.end_time = stop
            worktime.save()
            diff = worktime.end_time - worktime.start_time
            worktime.duration = diff.total_seconds()
            worktime.project = last_project.project
            worktime.save()
            if diff.total_seconds() >= 0:
                # ===== 12 godzin dniowki =======
                if diff.total_seconds() <= (60 * 60 * 12):
                    workday = WorkDay.objects.create(date=timezone.now().date(), amount_of_overhours=0,
                                                     type_of_workday='shooting day',
                                                     notes='', project_id=last_project.project.id)
                    workday.calculate_earnings()
                elif diff.total_seconds() > (60 * 60 * 12):
                    # ===== powyzej 12 godzin dniowki =======
                    overhours = math.ceil((diff.total_seconds() - (60 * 60 * 12)) / 3600)
                    workday = WorkDay.objects.create(date=timezone.now().date(), amount_of_overhours=overhours,
                                                     type_of_workday='shooting day',
                                                     notes='', project_id=last_project.project.id)
                    workday.calculate_earnings()

        workdays = WorkDay.objects.filter(project_id=last_project.project.id).count()
        projects = Project.objects.filter(user=request.user).order_by('-total_earnings_for_project')
        earnings = [x.total_earnings_for_project for x in projects]
        projects_names = [x.name for x in projects]
        chart = get_piechart(earnings, projects_names)
        return render(request, 'index.html',
                      {'last_project': last_project, 'workdays': workdays, 'button_select': button_select,
                       'chart': chart})


# ========================================================================================
# ===================================== user journey =====================================
# ---------------------------------------- REGISTER --------------------------------------

""" 
VIEW FOR Creating new user

#TODO: NEED TO CHANGE USER NAME FOR EMAIL AND ADD EMAIL AUTHENTICATION OPTION
"""


class RegisterUserView(CreateView):
    model = User
    form_class = RegisterUserForm
    template_name = 'user-register.html'
    success_url = reverse_lazy('login-user')

    def form_invalid(self, form):
        response = super().form_invalid(form)
        messages.error(self.request, 'Passwords are different or too common')
        return response


# ------------------------------------------ LOGIN ----------------------------------------
"""
SIMPLE LOGIN VIEW

:parameter
------------------
username: username
password: password

:return
------------------
Logged into user page

"""


class LoginUserView(LoginView):
    form_class = LoginForm
    template_name = 'user-login.html'
    next_page = reverse_lazy('main')


# ----------------------------------------- LOGOUT ----------------------------------------
"""
LOGOUT VIEW

:parameter
-----------
LOGGED USER

:return
-----------
Logged out
"""


class LogoutUserView(View):
    def get(self, request):
        logout(request)
        return redirect('main')


# ----------------------------------------- EDIT USER ----------------------------------------
"""
USER EDIT VIEW

:parameter
-----------
logged user

:return
----------
Edited User data
"""


class EditUserView(UpdateView):
    model = User
    fields = ['username', 'email', 'first_name', 'last_name']
    template_name = 'user-register.html'
    success_url = reverse_lazy('main')


# ============================================================================================
# ==================================== projects journey ======================================
# ------------------------------------ LIST OF PROJECTS --------------------------------------
"""
PROJECT LIST VIEW list of all created PROJECT for logged USER
"""


class ProjectListView(LoginRequiredMixin, View):
    login_url = reverse_lazy('login-user')

    def get(self, request):
        projects = Project.objects.filter(user=request.user).order_by("name")
        if projects.count() == 0:
            messages.add_message(request, messages.INFO, 'No projects')
        return render(request, 'project-list.html', {"projects": projects})


# ---------------------------------- ADDING PROJECTS -----------------------------------
"""
PROJECT CREATE VIEW

:parameters
------------
at least project name

:return
------------
add PROJECT to database for logged USER

"""


class ProjectAddView(LoginRequiredMixin, View):
    redirect_unauthenticated_users_to = 'register'

    def handle_no_permission(self):
        return HttpResponseRedirect(self.redirect_unauthenticated_users_to)

    def get(self, request):
        projects = Project.objects.filter(user_id=request.user.pk)
        if projects.count() == 0:
            messages.add_message(request, messages.INFO, 'No projects')
        productions = ProductionHouse.objects.filter(user=request.user)
        form = AddProjectForm()
        return render(request, 'project-add.html', {'form': form, 'projects': projects, "productions": productions})

    def post(self, request):
        form = AddProjectForm(request.POST)
        if form.is_valid():
            project = form.save(commit=False)
            project.user = request.user
            project.save()
            return redirect('project-list')
        else:
            return redirect('project-add')


# ------------------------------------- EDIT PROJECTS -----------------------------------

"""
EDIT PROJECT View for editing choose PROJECT

:parameter
-----------
selected PROJECT 

:return
-----------
edited PROJECT details

"""


class ProjectEditView(UserPassesTestMixin, View):
    def test_func(self):
        user = self.request.user
        project = Project.objects.get(pk=self.kwargs['pk'])
        return project.user == user

    def get(self, request, pk):
        if id is None:
            return redirect('main')
        try:
            project = Project.objects.get(pk=pk)
        except Project.DoesNotExist:
            return redirect('main')
        productions = ProductionHouse.objects.filter(user=request.user)
        form = EditProjectForm(instance=project)
        return render(request, 'project-edit.html', {"form": form, "project": project, "productions": productions})

    def post(self, request, pk):
        project = Project.objects.get(pk=pk)
        form = EditProjectForm(request.POST, instance=project)
        if form.is_valid():
            form.save()
            for day in WorkDay.objects.filter(project=project):
                day.calculate_earnings()
            return redirect('project-list')
        else:
            messages.error(request, 'Need to fill all necessary fields')
            return render(request, 'project-edit.html', {"form": form, "project": project})


# ------------------------------------- DELETING PROJECTS -----------------------------------
"""
PROJECT DELETE VIEW after login USER
confirm delete or go back to list of PROJECT LIST page

:parameters
-----------
LOGGED USER

:return
----------
deleted PROJECT object from database

"""


class ProjectDeleteView(LoginRequiredMixin, UserPassesTestMixin, DeleteView):
    login_url = reverse_lazy('login-user')

    def test_func(self):
        user = self.request.user
        project = Project.objects.get(pk=self.kwargs['pk'])
        return project.user == user

    model = Project
    success_url = reverse_lazy('project-list')
    template_name = 'project-delete.html'
    form_class = ProjectDeleteForm

    def form_valid(self, form):
        response = super().form_valid(form)
        messages.info(self.request, f'PROJECT : {self.object.name} DELETED SUCCESSFULLY')
        return response

    def form_invalid(self, form):
        return redirect('project-list')


# ===============================================================================================
# ======================================= DAYS JOURNEY ==========================================
# ------------------------------------- WORK DAY LIST VIEW --------------------------------------

"""
WORK DAY LIST VIEW for selected PROJECT for logged USER 
"""


class WorkDaysListView(LoginRequiredMixin, UserPassesTestMixin, View):
    login_url = reverse_lazy('login-user')

    def test_func(self):
        user = self.request.user
        project = Project.objects.get(pk=self.kwargs['pk'])
        return project.user == user

    def get(self, request, pk):
        daysofwork = WorkDay.objects.filter(project_id=pk).order_by('date')
        ### INFORMACJE PODSUMOWANIE PROJEKTU ###
        days_count = daysofwork.count()
        project_earned = WorkDay.objects.filter(project_id=pk).aggregate(sum=Sum('earnings'))
        project_earned = project_earned['sum']
        project = Project.objects.get(pk=pk)

        return render(request, 'workdays-list.html',
                      {"project": project, "daysofwork": daysofwork, "days_count": days_count,
                       "project_earned": project_earned})


# ------------------------------------- ADD WORK DAY VIEW ---------------------------------------
"""
WORK DAY CREATE VIEW

:parameters
------------
WORK DAY date and details

:return
------------
add WORK DAY to selected PROJECT and save to DATABASE

"""


class WorkDaysAddView(UserPassesTestMixin, View):
    login_url = reverse_lazy('login-user')

    def test_func(self):
        user = self.request.user
        project = Project.objects.get(pk=self.kwargs['pk'])
        return project.user == user

    def get(self, request, pk):
        workdays = WorkDay.objects.filter(project_id=pk).order_by('date')
        ### INFORMACJE PODSUMOWANIE PROJEKTU ###
        days_count = workdays.count()
        project_earned = WorkDay.objects.filter(project_id=pk).aggregate(sum=Sum('earnings'))
        project_earned = project_earned['sum']
        project = Project.objects.get(pk=pk)
        return render(request, 'workdays-add.html',
                      {"project": project, "daysofwork": workdays, "days_count": days_count,
                       "project_earned": project_earned})

    def post(self, request, pk):
        if request.POST.get('add_day'):
            date = request.POST.get('date')
            overhours = request.POST.get('overhours')
            type_of_day = request.POST.get('type_of_day')
            notes = request.POST.get('notes')
            if request.POST.get('percent_of_daily') != '':
                percent_of_daily = request.POST.get('percent_of_daily')
                type_of_day = percent_of_daily + '% of daily rate'
            if all([date, overhours, type_of_day]):
                added_day = WorkDay.objects.create(date=date, amount_of_overhours=overhours,
                                                   type_of_workday=type_of_day,
                                                   notes=notes, project_id=pk)
                added_day.calculate_earnings()
                return redirect('workdays-add', pk=pk)
            else:
                messages.add_message(request, messages.INFO, "Need to fill date")
                return redirect('workdays-add', pk=pk)


# ------------------------------------- EDITING WORK DAY -----------------------------------
"""
EDIT WORK DAY View for editing choose PROJECT

:parameter
-----------
selected WORK DAY 

:return
-----------
edited WORK DAY details

"""


class WorkDaysEditView(LoginRequiredMixin, UserPassesTestMixin, View):
    login_url = reverse_lazy('login-user')

    def test_func(self):
        user = self.request.user
        day = WorkDay.objects.get(pk=self.kwargs['pk'])
        return day.project.user == user

    def get(self, request, pk):
        workday = WorkDay.objects.get(pk=pk)
        # DLA DOMYSLNEJ DATY
        workday_date = str(workday.date)
        percent_amout_of_daily = ProductionHouse.just_numb(workday.type_of_workday)
        form = EditWorkDayForm(instance=workday)

        return render(request, 'workdays-edit.html', {'form': form, 'workday': workday, "workday_date": workday_date,
                                                      "percent_amout_of_daily": percent_amout_of_daily})

    def post(self, request, pk):
        day_of_work = WorkDay.objects.get(id=pk)
        form = EditWorkDayForm(request.POST, instance=day_of_work)
        if form.is_valid():
            if form.cleaned_data['type_of_workday'] == 'other':
                if form.cleaned_data['percent_of_daily'] is None:
                    day_of_work.type_of_workday = '100% of daily rate'
                else:
                    percent_of_daily = request.POST.get('percent_of_daily')
                    day_of_work.type_of_workday = percent_of_daily + '% of daily rate'
            form.save()
            day_of_work.calculate_earnings()
            return redirect('workdays-list', pk=day_of_work.project.id)
        else:
            messages.add_message(request, messages.INFO, "Need to fill date")
            return redirect('workdays-list', pk=day_of_work.project.pk)


# ------------------------------------- DELETING OF WORKING DAYS -----------------------------------
"""
WORK DAY DELETE VIEW after selecting PROJECT 
confirm delete or go back to list of WORK DAY page

:parameters
-----------
choose PROJECT

:return
----------
deleted WORK DAY object from database

"""


class WorkDaysDeleteView(LoginRequiredMixin, UserPassesTestMixin, DeleteView):
    login_url = reverse_lazy('login-user')

    def test_func(self):
        user = self.request.user
        day = WorkDay.objects.get(pk=self.kwargs['pk'])
        return day.project.user == user

    model = WorkDay
    template_name = 'workdays-delete.html'
    form_class = DaysDeleteForm

    def form_valid(self, form):
        response = super().form_valid(form)
        messages.info(self.request, f'DAY : {self.object.date} DELETED SUCCESSFULLY')
        return response

    def form_invalid(self, form):
        return redirect('workdays-list', pk=self.object.project.pk)

    def get_success_url(self):
        project_pk = self.object.project.pk
        return reverse_lazy('workdays-list', kwargs={'pk': project_pk})


# =======================================================================================
# ============================ PRODUCTION HOUSES JOURNEY ================================
# ----------------------------- PRODUCTION HOUSES LIST ----------------------------------

"""
PRODUCTION HOUSE LIST VIEW list of all created production houses for logged user
"""


class ProductionHousesListView(LoginRequiredMixin, View):
    login_url = reverse_lazy('login-user')

    def get(self, request):
        prod_houses = ProductionHouse.objects.filter(user=request.user)
        return render(request, 'production-list.html', {"prod_houses": prod_houses})


# ---------------------- ADDING PRODUCTION HOUSE AND NIP VALIDATE -------------------------
"""
PRODUCTION HOUSE CREATE VIEW with nip validator and error messages
for nip validator -> models.py -> ProductionHouses @staticmethod nip_checker

:parameters
------------
at least production house name

:return
------------
add production house to database

"""


class ProductionAddView(LoginRequiredMixin, View):
    login_url = reverse_lazy('login-user')

    def get(self, request, *args, **kwargs):
        form = AddProductionHouseForm
        return render(request, 'production-add.html', {'form': form})

    def post(self, request):
        form = AddProductionHouseForm(request.POST)
        if form.is_valid():
            prod_house = form.save(commit=False)
            prod_house.user = request.user
            if prod_house.nip:
                nip = str(prod_house.nip)
                if len(nip) != 10:
                    messages.add_message(request, messages.INFO, "LENGTH OF NIP NUMBER IS NOT CORRECT")
                    return render(request, 'production-add.html', {'form': form})
                else:
                    if ProductionHouse.nip_checker(nip) is True:
                        prod_house.nip = nip

                    else:
                        messages.add_message(request, messages.INFO, "NIP NUMBER IS NOT CORRECT")
                        return render(request, 'production-add.html', {'form': form})
            prod_house.save()
            return redirect('productions-list')
        else:
            return render(request, 'production-add.html', {'form': form})


# -----------------------------EDIT PRODUCTION HOUSES --------------------------


"""
EDIT PRODUCTION HOUSE View for editing choose production house with NIP VALIDATOR
for nip validator -> models.py -> ProductionHouses @staticmethod nip_checker

:parameter
-----------
selected PRODUCTION HOUSE

:return
-----------
edited PRODUCTION HOUSE details

"""


class ProductionEditView(LoginRequiredMixin, UserPassesTestMixin, View):
    login_url = reverse_lazy('login-user')

    def test_func(self):
        user = self.request.user
        productionhouse = ProductionHouse.objects.get(pk=self.kwargs['pk'])
        return productionhouse.user == user

    form_class = EditProductionForm
    template_name = 'production-edit.html'

    def get(self, request, *args, **kwargs):
        production_id = kwargs.get('pk')
        production = ProductionHouse.objects.get(pk=production_id)
        form = self.form_class(instance=production)
        return render(request, self.template_name, {'form': form})

    def post(self, request, *args, **kwargs):
        global validate_nip
        production_id = kwargs.get('pk')
        production = ProductionHouse.objects.get(pk=production_id)
        form = self.form_class(request.POST, instance=production)
        production.name = form['name'].value()
        if production.name == '':
            messages.add_message(request, messages.INFO, "NAME CANNOT BE EMPTY")
            return render(request, self.template_name, {'form': form})
        prod_nip = form['nip'].value()
        if prod_nip:
            if not all(char.isdigit() or char == '-' for char in prod_nip):
                messages.add_message(request, messages.INFO, "NIP NUMBER CAN USE ONLY DIGIT AND '-'")
                return render(request, self.template_name, {'form': form})
            else:
                clean_nip = prod_nip.replace('-', '')
                if len(clean_nip) != 10:
                    messages.add_message(request, messages.INFO, "LENGTH OF NIP NUMBER IS NOT CORRECT")
                    return render(request, self.template_name, {'form': form})
                else:
                    if ProductionHouse.nip_checker(clean_nip) is True:
                        validate_nip = clean_nip
                    else:
                        messages.add_message(request, messages.INFO, "NIP NUBER IS NOT CORRECT")
                        return render(request, self.template_name, {'form': form})
            production.nip = validate_nip
        production.address = form['address'].value()
        production.email = form['email'].value()
        production_rating = form['rating'].value()
        if production_rating == "":
            production.rating = None
        else:
            production.rating = form['rating'].value()
        production.notes = form['notes'].value()
        production.save()

        return redirect('productions-list')


# ----------------------- DELETING PRODUCTION HOUSE ---------------------------------
"""
PRODUCTION HOUSE DELETE VIEW after selecting contact 
confirm delete or go back to list of production house page

:parameters
-----------
choose production house

:return
----------
deleted production house object from database

"""


class ProductionHouseDeleteView(LoginRequiredMixin, UserPassesTestMixin, DeleteView):
    login_url = reverse_lazy('login-user')

    def test_func(self):
        user = self.request.user
        productionhouse = ProductionHouse.objects.get(pk=self.kwargs['pk'])
        return productionhouse.user == user

    model = ProductionHouse
    success_url = reverse_lazy('productions-list')
    template_name = 'productions-delete.html'
    form_class = ProductionHouseDeleteForm

    def form_valid(self, form):
        response = super().form_valid(form)
        messages.info(self.request, f'Production house : {self.object.name} DELETED SUCCESSFULLY')
        return response

    def form_invalid(self, form):
        return redirect('productions-list')


# =============================================================================
# ============================ CONTACT JOURNEY ================================
# ----------------------------- CONTACT LIST  ---------------------------------

"""
CONTACT LIST VIEW list of all created contacts for logged user

"""


class ContactListView(LoginRequiredMixin, View):
    login_url = reverse_lazy('login-user')

    def get(self, request):
        contacts = Contact.objects.filter(user=self.request.user).distinct('id')
        return render(request, 'contact-list.html', {'contacts': contacts})


# ----------------------------- CONTACT ADD  ----------------------------------
"""
CONTACT CREATE VIEW

:parameters
------------
at least name of contact 

:return
------------
add contact to database

"""


class ContactCreateView(LoginRequiredMixin, CreateView):
    login_url = reverse_lazy('login-user')
    model = Contact
    form_class = ContactAddForm
    success_url = reverse_lazy('contacts-list')
    template_name = 'contact-add.html'

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['user'] = self.request.user
        return kwargs

    def form_valid(self, form):
        form.instance.user = self.request.user
        return super().form_valid(form)

    def form_invalid(self, form):
        messages.info(self.request, "YOU DIDNT FILL FORM. CORRECTLY")
        return redirect('contacts-add')


# ----------------------------- CONTACT EDIT  ----------------------------------
"""
CONTACT EDIT VIEW

:parameter
-----------
selected contact

:return
-----------
edited contact details

"""


class ContactEditView(LoginRequiredMixin, UserPassesTestMixin, UpdateView):
    login_url = reverse_lazy('login-user')

    def test_func(self):
        user = self.request.user
        contact = Contact.objects.get(pk=self.kwargs['pk'])
        return contact.user == user

    model = Contact
    form_class = ContactAddForm
    success_url = reverse_lazy('contacts-list')
    template_name = 'contact-edit.html'

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['user'] = self.request.user
        return kwargs

    def form_invalid(self, form):
        messages.info(self.request, "YOU DIDNT FILL FORM. CORRECTLY")
        return redirect('contacts-add')


# ----------------------------- CONTACT DELETE  ----------------------------------
"""
CONTACT DELETE VIEW after selecting contact 
confirm delete or go back to list of contact page

:parameters
-----------
choose contact

:return
----------
deleted contact object from database

"""


class ContactDeleteView(LoginRequiredMixin, UserPassesTestMixin, DeleteView):
    login_url = reverse_lazy('login-user')

    def test_func(self):
        user = self.request.user
        contact = Contact.objects.get(pk=self.kwargs['pk'])
        return contact.user == user

    model = Contact
    success_url = reverse_lazy('contacts-list')
    template_name = 'contact-delete.html'
    form_class = ContactDeleteForm

    def form_valid(self, form):
        response = super().form_valid(form)
        messages.info(self.request, f'Contact : {self.object.first_name}  {self.object.last_name} DELETED SUCCESSFULLY')
        return response

    def form_invalid(self, form):
        return redirect('contacts-list')


# =======================================================================================
# ===================================  SEARCH JURNEY =====================================
"""
SEARCH VIEW base on selected options from html FORM
shows via GET method projects which meets selected requirements

:parameters
------------
DATE:
PROJECT NAME:
PRODUCTION HOUSES:
CONTACTS:

:return
------------
PROJECT WHICH MEETS SELECTED OPTIONS

"""


class SearchView(LoginRequiredMixin, View):
    login_url = reverse_lazy('login-user')

    def get(self, request):
        global filtred_projects
        filtred_projects = None

        all_projects = Project.objects.filter(user=self.request.user)
        all_work_days = WorkDay.objects.filter(project__in=all_projects).order_by('date')
        all_production_houses = ProductionHouse.objects.filter(user=self.request.user)
        all_contacts = Contact.objects.filter(user=self.request.user)
        date_start = request.GET.get('date_start')
        date_end = request.GET.get('date_end')

        if request.GET.get('project') is not None:
            selected_project = request.GET.getlist('project')
            all_work_days = WorkDay.objects.filter(project__name__in=selected_project).order_by('date')

        if request.GET.get('production') is not None:
            selected_production = request.GET.getlist('production')
            all_work_days = all_work_days.filter(
                project__production_house__name__in=selected_production).order_by(
                'date')
        if request.GET.get('contacts') is not None:
            selected_contacts = request.GET.getlist('contacts')
            all_work_days = all_work_days.filter(
                project__production_house__contact__first_name__in=selected_contacts).order_by(
                'date')

        if date_start and date_end:
            date_start = timezone.make_aware(datetime.strptime(date_start, '%Y-%m-%d'))
            date_end = timezone.make_aware(datetime.strptime(date_end, '%Y-%m-%d'))
            all_work_days = all_work_days.filter(date__range=[date_start, date_end])

        elif date_start:
            date_start = timezone.make_aware(datetime.strptime(date_start, '%Y-%m-%d'))
            all_work_days = all_work_days.filter(date__gte=date_start)

        elif date_end:
            date_end = timezone.make_aware(datetime.strptime(date_end, '%Y-%m-%d'))
            all_work_days = all_work_days.filter(date__lte=date_end)

        return render(request, 'search.html', {'all_projects': all_projects, 'all_work_days': all_work_days,
                                               'filtred_projects': filtred_projects,
                                               'all_production_houses': all_production_houses,
                                               'all_contacts': all_contacts, })


# ============ GENERATE PDF ================

"""
VIEW for generating pdf for selected PROJECT, with all days of work

:parameters
--------------
Project with at least one work day

:returns
--------------
PDF DOWNLOADABLE file with project summary 
"""


class CreatePdfView(View):
    font_path = os.path.join(settings.BASE_DIR, 'film_lifeapp/static/fonts/bitter/Bitter-Regular.ttf')
    pdfmetrics.registerFont(TTFont('Bitter', font_path))
    font_path2 = os.path.join(settings.BASE_DIR, 'film_lifeapp/static/fonts/bitter/Bitter-Bold.ttf')
    pdfmetrics.registerFont(TTFont('Bitter-Bold', font_path2))

    def get(self, request, pk):
        today = datetime.now().date()
        project = Project.objects.get(pk=pk)
        filename = f"{project.name}_date_of_create_{today}.pdf"
        buffer = create_pdf(project)
        return FileResponse(buffer, as_attachment=True, filename=filename)


# ============ SHOOTING SCHEDULE TO ICALENDAR ================
# Wyrażenie regularne do dopasowania dat


daysearchpl = re.compile(
    r'(?:(?:KONIEC DNIA|End Day|Koniec dnia zdjęciowego|END OF DAY|PODSUMOWANIE DNIA|End of Shooting Day)[^0-9]*?(?:nr|#|NR)?\s?(\d+)[^0-9]*?(\b(?:poniedziałek|wtorek|środa|czwartek|piątek|sobota|niedziela)\b)[^0-9]*(\d{1,2} \w+ \d{4}))|(\b(?:poniedziałek|wtorek|środa|czwartek|piątek|sobota|niedziela)\b, \d{1,2} \w+ \d{4})',
    re.IGNORECASE
)


def convert_date(date_str):
    return datetime.strptime(date_str, '%d %B %Y')


def extract_text_from_images(file_path):
    try:
        images = convert_from_path(file_path, dpi=300)
    except exceptions.PDFPageCountError as e:
        raise Exception(f"Failed to convert PDF to images: {e}")

    text = ""
    for image in images:
        text += pytesseract.image_to_string(image, lang='pol')
    return text


def process_pdf(file, project_name):
    locale.setlocale(locale.LC_TIME, 'pl_PL.UTF-8')
    pdf_content = None
    try:
        file.seek(0)
        pdf_content = file.read()
        if not pdf_content:
            raise Exception("PDF file is empty or could not be read.")

        pdf_text = extract_text(io.BytesIO(pdf_content))
    except Exception as e:
        print(f"Failed to extract text from PDF: {e}")
        pdf_text = ""

    matches = list(daysearchpl.finditer(pdf_text))
    if not matches and pdf_content:
        with tempfile.NamedTemporaryFile(delete=False, suffix='.pdf') as temp_pdf:
            temp_pdf.write(pdf_content)
            temp_pdf_path = temp_pdf.name


        try:
            pdf_text = extract_text_from_images(temp_pdf_path)
            print(pdf_text,'obraz na tekst')
            matches = list(daysearchpl.finditer(pdf_text))
        except Exception as e:
            print(f"Failed to convert PDF to images or extract text from images: {e}")
            raise Exception(f"Nie można odczytać pliku PDF: {e}")
        finally:
            os.remove(temp_pdf_path)

    events = []
    for match in matches:
        day_number = match.group(1)
        day_of_week = match.group(2)
        date_str = match.group(3)

        if not day_number or not day_of_week or not date_str:
            continue

        date = convert_date(date_str)
        event_name = f"{project_name} dzien: {day_number}"
        event = {
            "date": date,
            "description": event_name,
            "location": ""
        }
        events.append(event)

    cal = Calendar()
    for event in events:
        cal_event = Event()
        cal_event.name = event['description']
        cal_event.begin = event['date'].replace(tzinfo=None)
        cal_event.end = event['date'].replace(tzinfo=None)
        cal_event.description = event['description']
        cal_event.location = event['location']
        cal.events.add(cal_event)
    return cal


class CreateICalendar(LoginRequiredMixin, View):

    def get(self, request):
        form = PDFUploadForm()
        return render(request, 'pdftoicalendar.html', {'form': form})

    def post(self, request):
        form = PDFUploadForm(request.POST, request.FILES)
        if form.is_valid():
            project_name = form.cleaned_data['project_name']
            pdf_file = request.FILES.get('pdf_file')
            try:
                calendar = process_pdf(pdf_file, project_name)
                ical_content = calendar.serialize()
                response = HttpResponse(ical_content, content_type='text/calendar')
                response['Content-Disposition'] = f'attachment; filename="{project_name}_calendar.ics"'
                return response
            except Exception as e:
                form.add_error(None, str(e))
        return render(request, 'pdftoicalendar.html', {'form': form})