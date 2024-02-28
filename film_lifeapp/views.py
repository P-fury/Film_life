from django.http import HttpResponseRedirect, HttpResponse
from django.shortcuts import render, redirect
from django.views import View
from film_lifeapp.models import *
from django.core.paginator import Paginator
from django.db.models import Sum
from django.contrib import messages


# Create your views here.


class Main(View):
    def get(self, request):
        return render(request, 'index.html')


class ProjectList(View):
    def get(self, request):
        projects = Project.objects.all()
        if projects.count() == 0:
            messages.add_message(request, messages.INFO, 'No projects')
        return render(request, 'projects.html', {"projects": projects})


class ProjectAdd(View):
    def get(self, request):
        projects = Project.objects.all()

        return render(request, 'projects-add.html', {'projects': projects})

    def post(self, request):
        name = request.POST.get('name')
        daily_rate = request.POST.get('daily_rate')
        type_of_overhours = request.POST.get('type_of_overhours')
        occupation = request.POST.get('occupation')
        notes = request.POST.get('notes')
        if all([name, daily_rate, type_of_overhours, occupation]):
            Project.objects.create(name=name, daily_rate=daily_rate, type_of_overhours=type_of_overhours,
                                   occupation=occupation, notes=notes)
            return redirect('project-list')
        else:
            messages.add_message(request, messages.INFO, "Only NOTES can stay empty")
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

        date = request.POST.get('date')
        overhours = request.POST.get('overhours')
        type_of_day = request.POST.get('type_of_day')
        notes = request.POST.get('notes')
        print(request.POST.get('percent_of_daily'))
        if request.POST.get('percent_of_daily') is not None:
            percent_of_daily = request.POST.get('percent_of_daily')
            type_of_day = percent_of_daily + '% of daily rate'

        if all([date, overhours, type_of_day]):
            added_day = DayOfWork.objects.create(date=date, amount_of_overhours=overhours, type_of_workday=type_of_day,
                                                 notes=notes, project_id=id)
            added_day.calculate_earnings()
            return redirect('project-details', id=id)
