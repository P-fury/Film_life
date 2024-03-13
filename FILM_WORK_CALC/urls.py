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
from django.contrib import admin
from django.urls import path
from film_lifeapp import views

urlpatterns = [
    path('admin/', admin.site.urls),
    # ============ REDIRECT FOR VIEWERS WITHOUT LOGIN ===========
    path('<path:url>/register', views.RegisterUserView.as_view()),

    path('register_user/', views.RegisterUserView.as_view(), name='register-user'),
    path('login_user/', views.LoginUserView.as_view(), name='login-user'),
    path('logout_user/', views.LogoutUserView.as_view(), name='logout-user'),
    path('edit_user/<int:pk>/', views.EditUserView.as_view(), name='edit-user'),

    path('', views.MainView.as_view(), name='main'),

    path('project-list/', views.ProjectListView.as_view(), name='project-list'),
    path('project-details/<int:pk>/', views.ProjectDetailsView.as_view(), name='project-details'),
    path('project-add/', views.ProjectAddView.as_view(), name='project-add'),
    path('project-edit/<int:pk>/', views.ProjectEditView.as_view(), name='project-edit'),
    path('project-delete/<int:pk>/', views.ProjectDeleteView.as_view(), name='project-delete'),

    path('project/days/<int:pk>/', views.ProjectDaysView.as_view(), name='project-days'),
    path('project/days-delete/<int:pk>/', views.DaysDeleteView.as_view(), name='day-of-work-delete'),
    path('project/dayofwork/<int:pk>/', views.DayOfWorkDetailView.as_view(), name='day-of-work-details'),

    path('productions-list/', views.ProductionHousesListView.as_view(), name='productions-list'),
    path('productions-add/', views.ProductionAddView.as_view(), name='productions-add'),
    path('productions-edit/<int:pk>/', views.ProductionEditView.as_view(), name='productions-edit'),
    path('productions-delete/<int:pk>/', views.ProductionHouseDeleteView.as_view(), name='productions-delete'),


]
