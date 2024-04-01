import math
import os
from datetime import datetime, timezone
from django.contrib.auth import logout
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.contrib.auth.models import User
from django.contrib.auth.views import LoginView
from django.http import HttpResponseRedirect
from django.utils import timezone
from django.shortcuts import render, redirect
from django.urls import reverse_lazy
from django.views import View
from django.views.generic import CreateView, UpdateView, DeleteView
from ip2geotools.databases.noncommercial import DbIpCity

from film_lifeapp.forms import RegisterUserForm, LoginForm, EditProductionForm, ProjectDeleteForm, DaysDeleteForm, \
    ProductionHouseDeleteForm, ContactAddForm, ContactDeleteForm
from film_lifeapp.models import *
from django.db.models import Sum
from django.contrib import messages
from film_lifeapp.functions import nip_checker, create_pdf, find_timezone

# ========= PDF DOCU ====================
from django.http import FileResponse
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from film_lifeapp.utils import get_piechart


# Create your views here.
# ===================================== HOME JOURNEY ================================
# ------------------------------------- HOME PAGE -----------------------------------

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
class LoginUserView(LoginView):
    form_class = LoginForm
    template_name = 'user-login.html'
    next_page = reverse_lazy('main')


# ----------------------------------------- LOGOUT ----------------------------------------
class LogoutUserView(View):
    def get(self, request):
        logout(request)
        return redirect('main')


# ----------------------------------------- EDIT USER ----------------------------------------
class EditUserView(UpdateView):
    model = User
    fields = ['username', 'email', 'first_name', 'last_name']
    template_name = 'user-register.html'
    success_url = reverse_lazy('main')


# ============================================================================================
# ==================================== projects journey ======================================
# ------------------------------------ LIST OF PROJECTS --------------------------------------
class ProjectListView(LoginRequiredMixin, View):
    login_url = reverse_lazy('login-user')

    def get(self, request):
        projects = Project.objects.filter(user=request.user).order_by("name")
        if projects.count() == 0:
            messages.add_message(request, messages.INFO, 'No projects')
        return render(request, 'project-list.html', {"projects": projects})


# ---------------------------------- ADDING PROJECTS -----------------------------------
class ProjectAddView(LoginRequiredMixin, View):
    redirect_unauthenticated_users_to = 'register'

    def handle_no_permission(self):
        return HttpResponseRedirect(self.redirect_unauthenticated_users_to)

    def get(self, request):
        projects = Project.objects.filter(user_id=request.user.pk)
        if projects.count() == 0:
            messages.add_message(request, messages.INFO, 'No projects')
        productions = ProductionHouse.objects.filter(user=request.user)
        return render(request, 'project-add.html', {'projects': projects, "productions": productions})

    def post(self, request):
        name = request.POST.get('name')
        daily_rate = request.POST.get('daily_rate')
        type_of_overhours = request.POST.get('type_of_overhours')
        occupation = request.POST.get('occupation')
        notes = request.POST.get('notes')
        production = request.POST.get('production')
        if all([name, daily_rate, type_of_overhours]):
            Project.objects.create(name=name, daily_rate=daily_rate, type_of_overhours=type_of_overhours,
                                   occupation=occupation, notes=notes, production_house_id=production,
                                   user_id=request.user.id)
            return redirect('project-list')
        else:
            messages.error(request, 'Need to fill all fields')
            return redirect('project-add')


# ------------------------------------- EDIT PROJECTS -----------------------------------
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
        return render(request, 'project-edit.html', {"project": project, "productions": productions})

    def post(self, request, pk):
        project_to_edit = Project.objects.get(pk=pk)
        edited_name = request.POST.get('name')
        edited_daily_rate = request.POST.get('daily_rate')
        edited_type_of_overhours = request.POST.get('type_of_overhours')
        edited_occupation = request.POST.get('occupation')
        edited_notes = request.POST.get('notes')
        edited_production = request.POST.get('production')
        print(edited_production)
        if all([edited_name, edited_daily_rate, edited_type_of_overhours]):
            project_to_edit.name = edited_name
            project_to_edit.daily_rate = edited_daily_rate
            project_to_edit.type_of_overhours = edited_type_of_overhours
            project_to_edit.occupation = edited_occupation
            project_to_edit.notes = edited_notes
            if edited_production != '':
                project_to_edit.production_house_id = edited_production
            project_to_edit.save()
            for day in WorkDay.objects.filter(project_id=project_to_edit):
                day.calculate_earnings()
            # project_to_edit.update_project_total_earnings()
            return redirect('project-list')
        else:
            messages.error(request, 'Need to fill all necessary fields')
            return redirect('project-edit', pk=project_to_edit.pk)


# ------------------------------------- DELETING PROJECTS -----------------------------------
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
        percent_amout_of_daily = just_numb(workday.type_of_workday)
        print(percent_amout_of_daily)
        return render(request, 'workdays-edit.html', {'workday': workday, "workday_date": workday_date,
                                                      "percent_amout_of_daily": percent_amout_of_daily})

    def post(self, request, pk):
        day_of_work = WorkDay.objects.get(id=pk)
        date = request.POST.get('date')
        overhours = request.POST.get('overhours')
        type_of_day = request.POST.get('type_of_day')
        notes = request.POST.get('notes')
        if type_of_day == 'other':
            if request.POST.get('percent_of_daily') != '':
                percent_of_daily = request.POST.get('percent_of_daily')
                type_of_day = percent_of_daily + '% of daily rate'
            else:
                type_of_day = '100 % of daily rate'
        if all([date, overhours, type_of_day]):
            # NADPISYWANIE DANYCH
            day_of_work.date = date
            day_of_work.amount_of_overhours = overhours
            day_of_work.type_of_workday = type_of_day
            day_of_work.notes = notes
            day_of_work.save()
            day_of_work = WorkDay.objects.get(id=pk)
            day_of_work.calculate_earnings()
            return redirect('workdays-list', pk=day_of_work.project.id)
        else:
            messages.add_message(request, messages.INFO, "Need to fill date")
            return redirect('workdays-list', pk=day_of_work.project.pk)


# ------------------------------------- DELETING OF WORKING DAYS -----------------------------------
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
class ProductionHousesListView(LoginRequiredMixin, View):
    login_url = reverse_lazy('login-user')

    def get(self, request):
        prod_houses = ProductionHouse.objects.filter(user=request.user)
        return render(request, 'production-list.html', {"prod_houses": prod_houses})


# ---------------------- ADDING PRODUCTION HOUSE AND NIP VALIDATE -------------------------
class ProductionAddView(LoginRequiredMixin, View):
    login_url = reverse_lazy('login-user')

    def get(self, request):
        return render(request, 'production-add.html')

    def post(self, request):
        validate_nip = None
        prod_name = request.POST.get('name')
        if prod_name == '':
            messages.add_message(request, messages.INFO, "NEED TO FILL AT LEAST PROD. NAME")
            return render(request, 'production-add.html')
        prod_nip = request.POST.get('nip')
        if prod_nip:
            if not all(char.isdigit() or char == '-' for char in prod_nip):
                messages.add_message(request, messages.INFO, "NIP NUMBER CAN USE ONLY DIGIT AND '-' ")
                return render(request, 'production-add.html')
            else:
                clean_nip = prod_nip.replace('-', '')
                if len(clean_nip) != 10:
                    messages.add_message(request, messages.INFO, "LENGTH OF NIP NUMBER IS NOT CORRECT")
                    return render(request, 'production-add.html')
                else:
                    if nip_checker(clean_nip) is True:
                        validate_nip = clean_nip
                    else:
                        messages.add_message(request, messages.INFO, "NIP NUBER IS NOT CORRECT")
                        return render(request, 'production-add.html')
        # ============ NIP VALIDATE =========

        prod_address = request.POST.get('address')
        prod_email = request.POST.get('email')
        prod_notes = request.POST.get('notes')
        prod_rate = request.POST.get('rating')
        if ProductionHouse.objects.filter(name=prod_name).exists():
            messages.add_message(request, messages.INFO, "PRODUCTION EXIST")
            return render(request, 'production-add.html')
        else:
            ProductionHouse.objects.create(name=prod_name, nip=validate_nip, address=prod_address,
                                           email=prod_email, notes=prod_notes, rating=prod_rate, user=request.user)
            messages.add_message(request, messages.INFO, "PRODUCTION ADDED")
            return render(request, 'production-add.html')


# -----------------------------EDIT PRODUCTION HOUSES --------------------------
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
                    if nip_checker(clean_nip) is True:
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
class ContactListView(LoginRequiredMixin, View):
    login_url = reverse_lazy('login-user')

    def get(self, request):
        contacts = Contact.objects.filter(user=self.request.user).distinct('id')
        return render(request, 'contact-list.html', {'contacts': contacts})


# ----------------------------- CONTACT ADD  ----------------------------------
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
