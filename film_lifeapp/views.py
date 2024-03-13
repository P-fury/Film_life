import math
from datetime import datetime, timezone, timedelta
from django.contrib.auth import logout
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.contrib.auth.models import User
from django.contrib.auth.views import LoginView
from django.http import HttpResponseRedirect, JsonResponse
from django.utils import timezone
from django.shortcuts import render, redirect
from django.urls import reverse_lazy
from django.views import View
from django.views.generic import CreateView, TemplateView, UpdateView, DeleteView
from film_lifeapp.forms import RegisterUserForm, LoginForm, EditProductionForm, ProjectDeleteForm, DaysDeleteForm, \
    ProductionHouseDeleteForm
from film_lifeapp.models import *
from django.db.models import Sum
from django.contrib import messages
from film_lifeapp.functions import nip_checker


# Create your views here.
# ===================================== HOME JOURNEY ================================
# ------------------------------------- HOME PAGE -----------------------------------

class MainView(View):

    def get(self, request):
        button_select = True
        try:
            last_project = WorkDay.objects.filter(project__user=request.user).order_by('last_updated').last()
            if last_project != None:
                if last_project.project.user != request.user:
                    last_project = None
        except WorkDay.DoesNotExist and TypeError:
            return render(request, 'index.html')
        if last_project != None:
            if len(WorkDay.objects.all()) > 0:
                workdays = WorkDay.objects.filter(project__user=request.user).count()
            else:
                workdays = 0
        else:
            workdays = None
        return render(request, 'index.html',
                      {'last_project': last_project, 'workdays': workdays, 'button_select': button_select})

    def post(self, request):
        start_timer = datetime.now()
        stop = datetime.now()
        stop_timer = stop.strftime('%Y-%m-%d %H:%M:%S.%f')
        global worktime
        button_select = True

        try:
            last_project = WorkDay.objects.latest('last_updated')
        except WorkDay.DoesNotExist:
            return render(request, 'index.html')
        if request.POST.get('start-bt') == 'start':
            worktime = StartStop.objects.create(start_time=start_timer)
            button_select = False
        if request.POST.get('stop-bt'):
            button_select = True
            recive_time = request.POST.get('stop-bt')
            end_time = datetime.strptime(recive_time, '%Y-%m-%d %H:%M:%S.%f')
            worktime.end_time = end_time
            worktime.save()
            diff = worktime.end_time - worktime.start_time
            worktime.duration = diff.total_seconds()
            worktime.project = last_project.project
            worktime.save()
            if diff.total_seconds() >= 0:
                # ===== 12 godzin dniowki =======
                if diff.total_seconds() <= (60 * 60 * 12):
                    workday = WorkDay.objects.create(date=timezone.now().date(), amount_of_overhours=0,
                                                     type_of_workday='shoot_day',
                                                     notes='', project_id=last_project.project.id)
                    workday.calculate_earnings()
                elif diff.total_seconds() > (60 * 60 * 12):
                    # ===== powyzej 12 godzin dniowki =======
                    overhours = math.ceil((diff.total_seconds() - (60 * 60 * 12)) / 3600)
                    workday = WorkDay.objects.create(date=timezone.now().date(), amount_of_overhours=overhours,
                                                     type_of_workday='shoot_day',
                                                     notes='', project_id=last_project.project.id)
                    workday.calculate_earnings()

        workdays = WorkDay.objects.filter(project_id=last_project.project.id).count()
        return render(request, 'index.html',
                      {'last_project': last_project, 'workdays': workdays, 'button_select': button_select,
                       "stop_timer": stop_timer})


# ========================================================================================
# ===================================== user journey =====================================
# ---------------------------------------- REGISTER --------------------------------------


class RegisterUserView(CreateView):
    model = User
    form_class = RegisterUserForm
    template_name = 'register-user.html'
    success_url = reverse_lazy('login-user')

    def form_invalid(self, form):
        response = super().form_invalid(form)
        messages.info(self.request, 'Passwords are different')
        return response


# ------------------------------------------ LOGIN ----------------------------------------
class LoginUserView(LoginView):
    form_class = LoginForm
    template_name = 'login.html'
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
    template_name = 'register-user.html'
    success_url = reverse_lazy('main')


# ============================================================================================
# ==================================== projects journey ======================================
# ------------------------------------ LIST OF PROJECTS --------------------------------------
class ProjectListView(LoginRequiredMixin, View):
    redirect_unauthenticated_users_to = 'register'

    def handle_no_permission(self):
        return HttpResponseRedirect(self.redirect_unauthenticated_users_to)

    def get(self, request):
        projects = Project.objects.filter(user=request.user)
        if projects.count() == 0:
            messages.add_message(request, messages.INFO, 'No projects')
        return render(request, 'projects-list.html', {"projects": projects})


# ---------------------------------- ADDING PROJECTS -----------------------------------
class ProjectAddView(LoginRequiredMixin, View):
    redirect_unauthenticated_users_to = 'register'

    def handle_no_permission(self):
        return HttpResponseRedirect(self.redirect_unauthenticated_users_to)

    def get(self, request):
        projects = Project.objects.filter(user_id=request.user.pk)
        if projects.count() == 0:
            messages.add_message(request, messages.INFO, 'No projects')
        productions = ProductionHouse.objects.all()
        return render(request, 'projects-add.html', {'projects': projects, "productions": productions})

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
        productions = ProductionHouse.objects.all()
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
            return redirect('project-add')


# ------------------------------------- DELETING PROJECTS -----------------------------------
class ProjectDeleteView(LoginRequiredMixin, UserPassesTestMixin, DeleteView):
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
# ----------------------- PROJECT DETAILS AND ADDING QUICK WORKING DAY VIEW ---------------------
class ProjectDetailsView(UserPassesTestMixin, View):
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
        return render(request, 'project-details-add-day.html',
                      {"project": project, "daysofwork": workdays, "days_count": days_count,
                       "project_earned": project_earned})

    def post(self, request, pk):
        if 'add_day' in request.POST:
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
                return redirect('project-details', pk=pk)
            else:
                messages.add_message(request, messages.INFO, "Need to fill date")
                return redirect('project-details', pk=pk)


# ------------------------------------- EDITING OF ADDED WORKING DAY -----------------------------------
class DayOfWorkDetailView(UserPassesTestMixin, View):
    def test_func(self):
        user = self.request.user
        day = WorkDay.objects.get(pk=self.kwargs['pk'])
        return day.project.user == user

    def get(self, request, pk):
        print(WorkDay.objects.last())
        day_of_work = WorkDay.objects.get(pk=pk)
        # DLA DOMYSLNEJ DATY
        date_of_work = str(day_of_work.date)
        percent_amout_of_daily = just_numb(day_of_work.type_of_workday)
        return render(request, 'days-edit.html', {'day_of_work': day_of_work, "date_of_work": date_of_work,
                                                  "percent_amout_of_daily": percent_amout_of_daily})

    def post(self, request, pk):
        day_of_work = WorkDay.objects.get(id=pk)
        date = request.POST.get('date')
        overhours = request.POST.get('overhours')
        type_of_day = request.POST.get('type_of_day')
        print(type_of_day)
        notes = request.POST.get('notes')
        if type_of_day == 'other':
            if request.POST.get('percent_of_daily') != '':
                percent_of_daily = request.POST.get('percent_of_daily')
                type_of_day = percent_of_daily + '% of daily rate'
        if all([date, overhours, type_of_day]):
            # NADPISYWANIE DANYCH
            day_of_work.date = date
            day_of_work.amount_of_overhours = overhours
            day_of_work.type_of_workday = type_of_day
            day_of_work.notes = notes
            day_of_work.save()
            day_of_work = WorkDay.objects.get(id=pk)
            day_of_work.calculate_earnings()
            return redirect('project-details', pk=day_of_work.project.id)
        else:
            messages.add_message(request, messages.INFO, "Need to fill date")
            return redirect('project-details', pk=day_of_work.project.id)


# ------------------------------------- DELETING OF WORKING DAYS -----------------------------------
class DaysDeleteView(LoginRequiredMixin, UserPassesTestMixin, DeleteView):
    def test_func(self):
        user = self.request.user
        day = WorkDay.objects.get(pk=self.kwargs['pk'])
        return day.project.user == user

    model = WorkDay
    template_name = 'days-delete.html'
    form_class = DaysDeleteForm

    def form_valid(self, form):
        response = super().form_valid(form)
        messages.info(self.request, f'DAY : {self.object.date} DELETED SUCCESSFULLY')
        return response

    def form_invalid(self, form):
        return redirect('project-days', pk=self.object.project.pk)

    def get_success_url(self):
        project_pk = self.object.project.pk
        return reverse_lazy('project-days', kwargs={'pk': project_pk})


# ----------------------------- BASE WORKING DAYS VIEW AND TABLE ----------------------------
class ProjectDaysView(UserPassesTestMixin, View):
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

        return render(request, 'project-days.html',
                      {"project": project, "daysofwork": daysofwork, "days_count": days_count,
                       "project_earned": project_earned})


# =======================================================================================
# ============================ PRODUCTION HOUSES JOURNEY ================================
# ----------------------------- PRODUCTION HOUSES LIST ----------------------------------
class ProductionHousesListView(View):

    def get(self, request):
        prod_houses = ProductionHouse.objects.filter(user=request.user)
        return render(request, 'production-list.html', {"prod_houses": prod_houses})


# ---------------------- ADDING PRODUCTION HOUSE AND NIP VALIDATE -------------------------
class ProductionAddView(View):
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


# -----------------------------EDIT PRODUCTION HOUSES ----------------------------------------
class ProductionEditView(View):
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
        prod_nip = form['nip'].value()
        if prod_nip:
            if not all(char.isdigit() or char == '-' for char in prod_nip):
                messages.add_message(request, messages.INFO, "NIP NUMBER CAN USE ONLY DIGIT AND '-' ")
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


# ----------------------- DELETING PRODUCTION HOUSE -----------------------------------

class ProductionHouseDeleteView(UserPassesTestMixin, DeleteView):
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

# =======================================================================================
# ============================ CONTACT JOURNEY ================================
# ----------------------------- CONTACT LIST  ----------------------------------
