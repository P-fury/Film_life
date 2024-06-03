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
    path('project-add/', views.ProjectAddView.as_view(), name='project-add'),
    path('project-edit/<int:pk>/', views.ProjectEditView.as_view(), name='project-edit'),
    path('project-delete/<int:pk>/', views.ProjectDeleteView.as_view(), name='project-delete'),


    path('project/days/<int:pk>/', views.WorkDaysListView.as_view(), name='workdays-list'),
    path('project/<int:pk>/days-add/', views.WorkDaysAddView.as_view(), name='workdays-add'),
    path('project/workday/<int:pk>/', views.WorkDaysEditView.as_view(), name='workdays-edit'),
    path('project/days-delete/<int:pk>/', views.WorkDaysDeleteView.as_view(), name='workdays-delete'),

    path('productions-list/', views.ProductionHousesListView.as_view(), name='productions-list'),
    path('production-add/', views.ProductionAddView.as_view(), name='production-add'),
    path('production-edit/<int:pk>/', views.ProductionEditView.as_view(), name='production-edit'),
    path('production-delete/<int:pk>/', views.ProductionHouseDeleteView.as_view(), name='production-delete'),

    path('contacts-list/', views.ContactListView.as_view(), name='contacts-list'),
    path('contacts-add/', views.ContactCreateView.as_view(), name='contacts-add'),
    path('contacts-edit/<int:pk>/', views.ContactEditView.as_view(), name='contacts-edit'),
    path('contacts-delete/<int:pk>/', views.ContactDeleteView.as_view(), name='contacts-delete'),



    path('search_index/', views.SearchView.as_view(), name='search'),

    path('project_pdf/<int:pk>', views.CreatePdfView.as_view(), name='create-pdf'),


]
