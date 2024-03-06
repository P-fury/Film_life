"""
URL configuration for FILM_WORK_CALC project.

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
from film_lifeapp import views

urlpatterns = [
    path('', views.Main.as_view(), name='main'),
    path('project-list/', views.ProjectList.as_view(), name='project-list'),
    path('project-add/', views.ProjectAdd.as_view(), name='project-add'),
    path('project-edit/<id>/', views.ProjectEdit.as_view(), name='project-edit'),
    path('project/days/<id>/', views.ProjectDays.as_view(), name='project-days'),
    path('project-details/<id>/', views.ProjectDetails.as_view(), name='project-details'),
    path('project/dayofwork/<id>/', views.DayOfWorkDetailView.as_view(), name='day-of-work-details'),

    path('productions/list/', views.ProductionList.as_view(), name='productions-list'),
    path('productions/add/', views.AddProduction.as_view(), name='productions-add'),
]
