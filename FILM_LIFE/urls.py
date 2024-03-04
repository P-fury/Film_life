"""
URL configuration for FILM_LIFE project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.0/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.urls import path
from film_lifeapp.views import *

urlpatterns = [
    path('', Main.as_view(), name='main'),
    path('project-list/', ProjectList.as_view(), name='project-list'),
    path('project-add/', ProjectAdd.as_view(), name='project-add'),
    path('project-edit/<id>/', ProjectEdit.as_view(), name='project-edit'),
    path('project/days/<id>/', ProjectDays.as_view(), name='project-days'),
    path('project-details/<id>/', ProjectDetails.as_view(), name='project-details'),
    path('project/dayofwork/<id>/', DayOfWorkDetailView.as_view(), name='day-of-work-details'),

    path('productions/list/', ProductionList.as_view(), name='productions-list'),
    path('productions/add/', AddProduction.as_view(), name='productions-add'),
]
