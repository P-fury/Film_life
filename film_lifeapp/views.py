from django.http import HttpResponseRedirect, HttpResponse
from django.shortcuts import render, redirect
from django.views import View
from django.views.generic import DetailView

from film_lifeapp.models import *
from django.core.paginator import Paginator
from django.db.models import Sum
from django.contrib import messages

from django import forms
import widget_tweaks
from django.shortcuts import render


# Create your views here.


class Main(View):
    def get(self, request):
        return render(request, 'index.html')


class ProjectList(View):
    def get(self, request):
        projects = Project.objects.all()
        if projects.count() == 0:
            messages.add_message(request, messages.INFO, 'No projects')
        return render(request, 'projects-list.html', {"projects": projects})


class ProjectAdd(View):
    def get(self, request):
        projects = Project.objects.all()
        productions = ProductionHouse.objects.all()
        return render(request, 'projects-add.html', {'projects': projects, "productions": productions})

    def post(self, request):
        name = request.POST.get('name')
        daily_rate = request.POST.get('daily_rate')
        type_of_overhours = request.POST.get('type_of_overhours')
        occupation = request.POST.get('occupation')
        notes = request.POST.get('notes')
        production = request.POST.get('production')
        if all([name, daily_rate, type_of_overhours, occupation]):
            Project.objects.create(name=name, daily_rate=daily_rate, type_of_overhours=type_of_overhours,
                                   occupation=occupation, notes=notes, production_id=production)
            return redirect('project-list')
        else:
            messages.error(request, 'Need to fill all fields')
            return redirect('project-add')


class ProjectDetails(View):
    def get(self, request, id):
        daysofwork = DayOfWork.objects.filter(project_id=id).order_by('date')

        ### INFORMACJE PODSUMOWANIE PROJEKTU ###
        days_count = daysofwork.count()
        project_earned = DayOfWork.objects.filter(project_id=id).aggregate(sum=Sum('earnings'))
        project_earned = project_earned['sum']
        project = Project.objects.get(id=id)

        return render(request, 'project-details-add-day.html',
                      {"project": project, "daysofwork": daysofwork, "days_count": days_count,
                       "project_earned": project_earned})

    def post(self, request, id):
        if 'add_day' in request.POST:
            date = request.POST.get('date')
            overhours = request.POST.get('overhours')
            type_of_day = request.POST.get('type_of_day')
            notes = request.POST.get('notes')
            if request.POST.get('percent_of_daily') != '':
                percent_of_daily = request.POST.get('percent_of_daily')
                type_of_day = percent_of_daily + '% of daily rate'

            if all([date, overhours, type_of_day]):
                added_day = DayOfWork.objects.create(date=date, amount_of_overhours=overhours,
                                                     type_of_workday=type_of_day,
                                                     notes=notes, project_id=id)
                added_day.calculate_earnings()
                return redirect('project-details', id=id)
            else:
                messages.add_message(request, messages.INFO, "Need to fill date")
                return redirect('project-details', id=id)

        elif 'edit_day' in request.POST:
            day_id = request.POST.get('edit_day')
            return redirect('day-of-work-details', id=day_id)


class DayOfWorkDetailView(View):
    def get(self, request, id):
        day_of_work = DayOfWork.objects.get(id=id)
        # DLA DOMYSLNEJ DATY
        date_of_work = str(day_of_work.date)
        percent_amout_of_daily = just_numb(day_of_work.type_of_workday)

        return render(request, 'days-edit.html', {'day_of_work': day_of_work, "date_of_work": date_of_work,
                                                  "percent_amout_of_daily": percent_amout_of_daily})

    def post(self, request, id):
        day_of_work = DayOfWork.objects.get(id=id)
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
            day_of_work = DayOfWork.objects.get(id=id)
            day_of_work.calculate_earnings()
            return redirect('project-details', id=day_of_work.project.id)
        else:
            messages.add_message(request, messages.INFO, "Need to fill date")
            return redirect('project-details', id=day_of_work.project.id)


# ----------------------------- OBSLUGA DNI ----------------------------
class ProjectDays(View):
    def get(self, request, id):
        daysofwork = DayOfWork.objects.filter(project_id=id).order_by('date')
        ### INFORMACJE PODSUMOWANIE PROJEKTU ###
        days_count = daysofwork.count()
        project_earned = DayOfWork.objects.filter(project_id=id).aggregate(sum=Sum('earnings'))
        project_earned = project_earned['sum']
        project = Project.objects.get(id=id)

        return render(request, 'project-days.html',
                      {"project": project, "daysofwork": daysofwork, "days_count": days_count,
                       "project_earned": project_earned})

    def post(self, request, id):
        if 'edit_day' in request.POST:
            day_id = request.POST.get('edit_day')
            return redirect('day-of-work-details', id=day_id)


# ------------ PRODUCTION HOUSES AND CONTACTS -------------------
class ProductionList(View):
    def get(self, request):
        prod_houses = ProductionHouse.objects.all()
        return render(request, 'production-list.html', {"prod_houses": prod_houses})


class AddProduction(View):
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
                    wagi = [6, 5, 7, 2, 3, 4, 5, 6, 7]
                    lst = [int(number) for number in clean_nip[:-1]]
                    result = [waga * cyfra for waga, cyfra in zip(wagi, lst)]
                    if sum(result) % 11 == int(clean_nip[-1]):
                        validate_nip = clean_nip
        #             ALGORYTM POPRAWNOSCI NIP

        prod_address = request.POST.get('address')
        prod_email = request.POST.get('email')
        prod_notes = request.POST.get('notes')
        prod_rate = request.POST.get('rating')
        if ProductionHouse.objects.filter(name=prod_name).exists():
            messages.add_message(request, messages.INFO, "PRODUCTION EXIST")
            return render(request, 'production-add.html')
        else:
            ProductionHouse.objects.create(name=prod_name, nip=validate_nip, address=prod_address,
                                           email=prod_email, notes=prod_notes, rating=prod_rate)
            messages.add_message(request, messages.INFO, "PRODUCTION ADDED")
            return render(request, 'production-add.html')
