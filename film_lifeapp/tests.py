from datetime import datetime, timedelta
from django.contrib.auth.models import User
from django.contrib.messages import get_messages
from django.core.exceptions import ObjectDoesNotExist
from pycparser.ply.yacc import Production
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.support import expected_conditions
from film_lifeapp.functions import nip_checker
import pytest
from django.urls import reverse, reverse_lazy
from django.test import Client
from film_lifeapp.models import StartStop, Project, WorkDay, ProductionHouse, Contact
from django.test import LiveServerTestCase


# Create your tests here.

# -------------------------- NIP CHECKER ----------------------------------
def test_nip_checker_len_to_short():
    nip = '87483'
    assert nip_checker(nip) is False


def test_nip_checker_len_to_long():
    nip = '8744566543383'
    assert nip_checker(nip) is False


def test_nip_checker_len_10_but_contains_letter():
    nip = '52679A9480'
    assert nip_checker(nip) is False


def test_nip_checker_len_10_but_false_number():
    nip = '5267979480'
    assert nip_checker(nip) is False


def test_nip_checker_nip_is_correct():
    nip = '8121230134'
    assert nip_checker(nip) is True


# ================== REGISTER USER =============================
def test_register_user_get():
    client = Client()
    url = reverse('register-user')
    response = client.get(url)
    assert response.status_code == 200


@pytest.mark.django_db
def test_register_user_post_different_passwords():
    client = Client()
    url = reverse('register-user')
    data = {'username': 'test', 'password1': '<PASSWORD>', 'password2': '<PASSWORD2>'}
    response = client.post(url, data)
    messages = list(response.context['messages'])
    assert response.status_code == 200
    assert str(messages[0]) == 'Passwords are different'


@pytest.mark.django_db
def test_register_user_post_correct_password():
    client = Client()
    url = reverse('register-user')
    data = {'username': 'testuser', 'password1': 'passwordtest', 'password2': 'passwordtest'}
    response = client.post(url, data)
    assert response.status_code == 302
    usercheck = User.objects.get(username='testuser')


# ======================== LOGIN-LOGOUT ===========================


def test_login_get():
    client = Client()
    url = reverse('login-user')
    response = client.get(url)
    assert response.status_code == 200


@pytest.mark.django_db
def test_login_wrong_login(user):
    client = Client()
    url = reverse('login-user')
    data = {'username': user.username, 'password': 'wrong'}
    response = client.post(url, data)
    assert response.status_code == 200
    print(response.context['user'])


@pytest.mark.django_db
def test_login_correct_login(user):
    client = Client()
    url = reverse('login-user')
    data = {'username': user.username, 'password': '<PASSWORD>'}
    response = client.post(url, data, follow=True)
    assert response.status_code == 200
    assert user.is_authenticated
    assert response.context['user'] == user
    print(response.context['user'])


@pytest.mark.django_db
def test_login_force_login(user):
    client = Client()
    url = reverse('login-user')
    client.force_login(user)
    response = client.get(url)
    assert response.status_code == 200
    assert user.is_authenticated
    assert response.context['user'] == user


@pytest.mark.django_db
def test_logout(user):
    client = Client()
    client.force_login(user)
    url = reverse('logout-user')
    response = client.get(url, follow=True)
    assert response.status_code == 200
    assert not response.context['user'] == user


# ================== MAIN VIEW =============================
@pytest.mark.django_db
def test_main_get_without_db():
    client = Client()
    url = reverse('main')
    response = client.get(url, {})
    assert response.status_code == 200


@pytest.mark.django_db
def test_main_get_logged(user_with_db):
    client = Client()
    url = reverse('main')
    client.force_login(user_with_db[0])
    response = client.get(url, {})
    assert response.status_code == 200
    assert response.context['last_project'].project == user_with_db[1]


@pytest.mark.django_db
def test_main_post_logged_start(user_with_db):
    client = Client()
    url = reverse('main')
    client.force_login(user_with_db[0])
    response = client.post(url, {'start-bt': 'start'})
    assert response.status_code == 200
    assert StartStop.objects.all().count() == 1
    print(StartStop.objects.last().start_time)


@pytest.mark.django_db
def test_main_post_logged_start_stop_validate_by_earnings_column(user_with_db):
    client = Client()
    url = reverse('main')
    client.force_login(user_with_db[0])
    end = datetime.now() + timedelta(hours=12, seconds=14)
    response = client.post(url, {'start-bt': 'start'})
    assert user_with_db[1].workday_set.count() == 1
    assert response.status_code == 200
    assert StartStop.objects.all().count() == 1
    response = client.post(url, {'stop-bt': end})
    assert user_with_db[1].workday_set.count() == 2
    user_with_db[1].refresh_from_db()
    assert user_with_db[1].workday_set.order_by('-last_updated').first().amount_of_overhours == 1
    user_with_db[1].refresh_from_db()
    # ====== TWO WORKING DAYS AND ONE OVERHOUR ============
    earinings = ((int(user_with_db[1].type_of_overhours) / 100)
                 * user_with_db[1].daily_rate + 2 * user_with_db[1].daily_rate)
    assert user_with_db[1].total_earnings_for_project == earinings


# ================== LIST OF PROJECT  VIEW =============================
@pytest.mark.django_db
def test_project_list_get_without_db():
    client = Client()
    url = reverse('project-list')
    response = client.get(url, follow=True)
    assert response.status_code == 200
    redirect_chain = response.redirect_chain
    if redirect_chain:
        final_url, statushttp = redirect_chain[-1]
        assert final_url == '/register_user/?next=/project-list/'
        assert statushttp == 302


@pytest.mark.django_db
def test_project_list_get(user_with_db):
    client = Client()
    client.force_login(user_with_db[0])
    url = reverse('project-list')
    response = client.get(url)
    assert response.status_code == 200
    assert not response.context['projects'] is None
    assert response.context['projects'].count() == 1
    for project in response.context['projects']:
        assert project.name == user_with_db[1].name


# ======================   ADD PROJECT VIEW =============================
@pytest.mark.django_db
def test_project_add_get_without_login():
    client = Client()
    url = reverse('project-add')
    response = client.get(url)
    assert response.status_code == 302


@pytest.mark.django_db
def test_project_add_get_with_login(user_with_db):
    client = Client()
    client.force_login(user_with_db[0])
    url = reverse('project-add')
    response = client.get(url)
    assert response.status_code == 200
    assert response.context['projects'].count() == 1


@pytest.mark.django_db
def test_project_add_post_login(user_with_db, project_add_form):
    client = Client()
    client.force_login(user_with_db[0])
    url = reverse('project-add')
    response = client.post(url, project_add_form, follow=True)
    assert response.status_code == 200
    assert response.context['projects'].count() == 2


# ======================   EDIT PROJECT VIEW =============================

@pytest.mark.django_db
def test_project_edit_get_with_login(user_with_db):
    client = Client()
    client.force_login(user_with_db[0])
    url = reverse('project-edit', args=[user_with_db[1].pk])
    response = client.get(url, follow=True)
    assert response.status_code == 200
    assert response.context['project'] == user_with_db[1]


@pytest.mark.django_db
def test_project_edit_get_with_login_wrong_id_in_URL(user_with_db):
    client = Client()
    client.force_login(user_with_db[0])
    url = reverse('project-edit', args=['77'])
    with pytest.raises(ObjectDoesNotExist):
        client.get(url, follow=True)


@pytest.mark.django_db
def test_project_edit_post_with_login(user_with_db, project_edit_form):
    client = Client()
    client.force_login(user_with_db[0])
    url = reverse('project-edit', args=[user_with_db[1].pk])
    assert user_with_db[1].name != project_edit_form['name']
    response = client.post(url, project_edit_form, follow=True)
    assert response.status_code == 200
    for detail in response.context['projects']:
        assert detail.name == project_edit_form['name']


@pytest.mark.django_db
def test_project_edit_post_with_login_empty_name(user_with_db):
    client = Client()
    data = {
        'name': '',
        'daily_rate': 100,
        'type_of_overhours': 14
    }
    client.force_login(user_with_db[0])
    url = reverse('project-edit', args=[user_with_db[1].pk])
    response = client.post(url, data, follow=True)
    assert response.status_code == 200
    storage = get_messages(response.wsgi_request)
    error_messages = [msg.message for msg in storage if msg.tags == 'error']
    assert len(error_messages) == 1
    assert error_messages[0] == 'Need to fill all necessary fields'


# ======================  DELETE PROJECT VIEW =============================
@pytest.mark.django_db
def test_project_delete_get_with_login(user_with_db):
    client = Client()
    client.force_login(user_with_db[0])
    url = reverse('project-delete', args=[user_with_db[1].pk])
    response = client.get(url)
    assert response.status_code == 200
    assert response.context['project'] == user_with_db[1]


@pytest.mark.django_db
def test_project_delete_post_dont_delete_with_login(user_with_db):
    client = Client()
    client.force_login(user_with_db[0])
    url = reverse('project-delete', args=[user_with_db[1].pk])
    initial_count = Project.objects.count()
    data = {'action': 'NO'}
    response = client.post(url, data)
    assert response.status_code == 302
    assert Project.objects.count() == initial_count


@pytest.mark.django_db
def test_project_delete_post_delete_with_login(user_with_db):
    client = Client()
    client.force_login(user_with_db[0])
    url = reverse('project-delete', args=[user_with_db[1].pk])
    initial_count = Project.objects.count()
    data = {'action': 'YES'}
    response = client.post(url, data)
    assert response.status_code == 302
    assert Project.objects.count() == initial_count - 1


# ======================= WORKDAYS =====================
# ================== WORK DAYS LIST =============================

@pytest.mark.django_db
def test_workday_list_get_without_login(project_test):
    client = Client()
    url = reverse('workdays-list', args=[project_test.pk])
    response = client.get(url, follow=True)
    assert response.status_code == 200
    redirect_chain = response.redirect_chain
    if redirect_chain:
        final_url, statushttp = redirect_chain[-1]
        assert final_url == f'/register_user/?next=/project/days/{project_test.id}/'
        assert statushttp == 302


@pytest.mark.django_db
def test_workday_list_get_with_login(user_with_db):
    client = Client()
    client.force_login(user_with_db[0])
    url = reverse('workdays-list', args=[user_with_db[1].pk])
    response = client.get(url)
    assert response.status_code == 200
    assert response.context['project'] == user_with_db[1]


# ==================  ADD WORKDAYS VIEW =============================
@pytest.mark.django_db
def test_workday_add_get_without_login(project_test):
    client = Client()
    url = reverse('workdays-add', args=[project_test.id])
    response = client.get(url, follow=True)
    assert response.status_code == 200
    redirect_chain = response.redirect_chain
    if redirect_chain:
        final_url, statushttp = redirect_chain[-1]
        assert final_url == f'/register_user/?next=/project/{project_test.id}/days-add/'
        assert statushttp == 302


@pytest.mark.django_db
def test_workday_add_get_with_login(user_with_db):
    client = Client()
    client.force_login(user_with_db[0])
    url = reverse('workdays-add', args=[user_with_db[1].pk])
    response = client.get(url)
    assert response.status_code == 200
    assert response.context['project'] == user_with_db[1]


@pytest.mark.django_db
def test_workday_add_post_with_login(user_with_db, workday_add_form):
    client = Client()
    client.force_login(user_with_db[0])
    url = reverse('workdays-add', args=[user_with_db[1].pk])
    inital_workdays = WorkDay.objects.count()
    response = client.post(url, data=workday_add_form)
    assert response.status_code == 302
    assert WorkDay.objects.count() == inital_workdays + 1


@pytest.mark.django_db
def test_workday_add_post_no_date_with_login(user_with_db):
    client = Client()
    client.force_login(user_with_db[0])
    url = reverse('workdays-add', args=[user_with_db[1].pk])
    data = {
        'date': '',
        'overhours': '0',
        'type_of_day': 'shooting day',
        'notes': '',
        'percent_of_daily': '',
    }
    inital_workdays = WorkDay.objects.count()
    response = client.post(url, data=data)
    assert response.status_code == 302
    assert WorkDay.objects.count() == inital_workdays
    storage = get_messages(response.wsgi_request)
    messages = [msg.message for msg in storage]
    assert len(messages) == 1
    assert messages[0] == 'Need to fill date'


# ==================  EDIT  WORK DAY VIEW =============================


@pytest.mark.django_db
def test_workday_edit_get_without_login(user_with_db):
    client = Client()
    url = reverse('workdays-edit', args=[user_with_db[2].pk])
    response = client.get(url, follow=True)
    assert response.status_code == 200
    redirect_chain = response.redirect_chain
    if redirect_chain:
        final_url, statushttp = redirect_chain[-1]
        assert final_url == f'/register_user/?next=/project/workday/{user_with_db[2].pk}/'
        assert statushttp == 302


@pytest.mark.django_db
def test_workday_edit_get_with_login(user_with_db):
    client = Client()
    client.force_login(user_with_db[0])
    workday = user_with_db[2]
    url = reverse('workdays-edit', args=[user_with_db[2].pk])
    response = client.get(url, follow=True)
    assert response.status_code == 200
    date = user_with_db[2].date
    # ---- SPRAWDZA ZAWARTOSC HTML------
    assert f'value="{workday.date}"' in response.content.decode('utf-8')


@pytest.mark.django_db
def test_workday_edit_post_with_login(user_with_db, workday_add_form):
    client = Client()
    client.force_login(user_with_db[0])
    initial_date = user_with_db[2].date
    initial_workday = WorkDay.objects.count()
    url = reverse('workdays-edit', args=[user_with_db[2].pk])
    response = client.post(url, workday_add_form, follow=True)
    assert response.status_code == 200
    assert WorkDay.objects.filter(date=workday_add_form['date']).exists()
    assert WorkDay.objects.count() == initial_workday


@pytest.mark.django_db
def test_workday_edit_post_with_login_no_date(user_with_db):
    client = Client()
    client.force_login(user_with_db[0])
    data = {
        'date': '',
        'overhours': 0,
        'type_of_day': 'shooting day',
        'notes': '',
        'percent_of_daily': '',
    }
    initial_date = user_with_db[2].date
    initial_workday = WorkDay.objects.count()
    url = reverse('workdays-edit', args=[user_with_db[2].pk])
    response = client.post(url, data, follow=True)
    assert response.status_code == 200
    storage = get_messages(response.wsgi_request)
    messages = [msg.message for msg in storage]
    assert len(messages) == 1
    assert messages[0] == 'Need to fill date'
    assert WorkDay.objects.count() == initial_workday
    assert WorkDay.objects.filter(date=initial_date).exists()


@pytest.mark.django_db
def test_workday_edit_post_with_login_other_sixtyfour_percent_of_daily(user_with_db):
    client = Client()
    client.force_login(user_with_db[0])
    data = {
        'date': '2021-01-01',
        'overhours': 0,
        'type_of_day': 'other',
        'notes': '',
        'percent_of_daily': '64',
    }
    initial_total_ernings_of_project = user_with_db[1].total_earnings_for_project
    initial_workday = WorkDay.objects.count()
    url = reverse('workdays-edit', args=[user_with_db[2].pk])
    response = client.post(url, data, follow=True)
    user_with_db[1].refresh_from_db()
    after_update_total_earnings_of_project = user_with_db[1].total_earnings_for_project
    assert response.status_code == 200
    assert WorkDay.objects.count() == initial_workday
    assert not initial_total_ernings_of_project == user_with_db[1].total_earnings_for_project
    assert after_update_total_earnings_of_project == user_with_db[1].daily_rate * 0.64


@pytest.mark.django_db
def test_workday_edit_post_with_login_transport_fifty_percent_of_daily(user_with_db):
    client = Client()
    client.force_login(user_with_db[0])
    data = {
        'date': '2021-01-01',
        'overhours': 0,
        'type_of_day': 'transport',
        'notes': '',
        'percent_of_daily': '',
    }
    initial_total_ernings_of_project = user_with_db[1].total_earnings_for_project
    initial_workday = WorkDay.objects.count()
    url = reverse('workdays-edit', args=[user_with_db[2].pk])
    response = client.post(url, data, follow=True)
    user_with_db[1].refresh_from_db()
    after_update_total_earnings_of_project = user_with_db[1].total_earnings_for_project
    assert response.status_code == 200
    assert WorkDay.objects.count() == initial_workday
    assert not initial_total_ernings_of_project == user_with_db[1].total_earnings_for_project
    assert after_update_total_earnings_of_project == user_with_db[1].daily_rate * 0.50


# ================== DELETE WORK DAY VIEW =============================


@pytest.mark.django_db
def test_workday_edit_get_without_login(user_with_db):
    client = Client()
    url = reverse('workdays-delete', args=[user_with_db[2].pk])
    response = client.get(url, follow=True)
    assert response.status_code == 200
    redirect_chain = response.redirect_chain
    if redirect_chain:
        final_url, statushttp = redirect_chain[-1]
        assert final_url == f'/register_user/?next=/project/days-delete/{user_with_db[2].pk}/'
        assert statushttp == 302


@pytest.mark.django_db
def test_workday_edit_get_with_login(user_with_db):
    client = Client()
    client.force_login(user_with_db[0])
    url = reverse('workdays-delete', args=[user_with_db[2].pk])
    response = client.get(url, follow=True)
    assert response.status_code == 200
    assert response.context['workday'] == user_with_db[2]


@pytest.mark.django_db
def test_workday_edit_post_with_login_delete_no(user_with_db):
    client = Client()
    client.force_login(user_with_db[0])
    url = reverse('workdays-delete', args=[user_with_db[2].pk])
    data = {
        'action': 'NO',
    }
    initial_workday = WorkDay.objects.first()
    initial_count_workday = WorkDay.objects.count()
    response = client.post(url, data, follow=True)
    assert response.status_code == 200
    assert initial_workday == WorkDay.objects.first()
    assert initial_count_workday == WorkDay.objects.count()


@pytest.mark.django_db
def test_workday_edit_post_with_login_delete_yes(user_with_db):
    client = Client()
    client.force_login(user_with_db[0])
    url = reverse('workdays-delete', args=[user_with_db[2].pk])
    data = {
        'action': 'YES',
    }
    initial_workday = WorkDay.objects.first()
    response = client.post(url, data, follow=True)
    assert response.status_code == 200
    assert not WorkDay.objects.first() == initial_workday


# ======================= PRODUCTION HOUSE =====================
# ================== PRODUCTION HOUSE LIST =============================


@pytest.mark.django_db
def test_production_house_list_get_without_login(production_house_db):
    client = Client()
    url = reverse('productions-list')
    response = client.get(url, follow=True)
    assert response.status_code == 200
    redirect_chain = response.redirect_chain
    if redirect_chain:
        final_url, statushttp = redirect_chain[-1]
        assert final_url == f'/register_user/?next=/productions-list/'
        assert statushttp == 302


# ------- PRODUCTION HOUSE WITHOUS USER AS OWNER ---------
@pytest.mark.django_db
def test_production_house_list_get_with_login(user_with_db, production_house_db):
    client = Client()
    client.force_login(user_with_db[0])
    url = reverse('productions-list')
    response = client.get(url)
    assert response.status_code == 200
    assert not response.context['prod_houses'] == production_house_db


@pytest.mark.django_db
def test_production_house_list_get_with_login(user_with_db, production_house_owner_user_with_db):
    client = Client()
    client.force_login(user_with_db[0])
    url = reverse('productions-list')
    response = client.get(url)
    assert response.status_code == 200
    for house in response.context['prod_houses']:
        assert house == production_house_owner_user_with_db


# ================== PRODUCTION HOUSE ADD VIEW =============================


@pytest.mark.django_db
def test_production_house_add_get_without_login(production_house_db):
    client = Client()
    url = reverse('production-add')
    response = client.get(url, follow=True)
    assert response.status_code == 200
    redirect_chain = response.redirect_chain
    if redirect_chain:
        final_url, statushttp = redirect_chain[-1]
        assert final_url == f'/register_user/?next=/production-add/'
        assert statushttp == 302


@pytest.mark.django_db
def test_production_house_add_post_with_login(user_with_db, production_house_add_form_owner_user_with_db):
    client = Client()
    client.force_login(user_with_db[0])
    url = reverse('production-add')
    initial_counter = ProductionHouse.objects.count()
    added_prod_house = production_house_add_form_owner_user_with_db
    response = client.post(url, production_house_add_form_owner_user_with_db)
    assert response.status_code == 200
    assert ProductionHouse.objects.filter(user=user_with_db[0]).count() == initial_counter + 1


@pytest.mark.django_db
def test_production_house_add_post_no_name_with_login(user_with_db):
    client = Client()
    client.force_login(user_with_db[0])
    url = reverse('production-add')
    data = {
        'name': '',
        'nip': '9512354036',
        'address': 'test form address',
        'email': 'form@prodtest.pl',
        'rating': 5,
        'notes': 'test notes',

    }
    inital_workdays = ProductionHouse.objects.count()
    response = client.post(url, data)
    assert response.status_code == 200
    assert ProductionHouse.objects.count() == inital_workdays
    storage = get_messages(response.wsgi_request)
    messages = [msg.message for msg in storage]
    assert len(messages) == 1
    assert messages[0] == 'NEED TO FILL AT LEAST PROD. NAME'


@pytest.mark.django_db
def test_production_house_add_post_nip_to_short_with_login(user_with_db):
    client = Client()
    client.force_login(user_with_db[0])
    url = reverse('production-add')
    data = {
        'name': 'test_form_production_house',
        'nip': '951236',
        'address': 'test form address',
        'email': 'form@prodtest.pl',
        'rating': 5,
        'notes': 'test notes',

    }
    inital_workdays = ProductionHouse.objects.count()
    response = client.post(url, data)
    assert response.status_code == 200
    assert ProductionHouse.objects.count() == inital_workdays
    storage = get_messages(response.wsgi_request)
    messages = [msg.message for msg in storage]
    assert len(messages) == 1
    assert messages[0] == 'LENGTH OF NIP NUMBER IS NOT CORRECT'


@pytest.mark.django_db
def test_production_house_add_post_nip_wrong_with_login(user_with_db):
    client = Client()
    client.force_login(user_with_db[0])
    url = reverse('production-add')
    data = {
        'name': 'test_form_production_house',
        'nip': '1234567890',
        'address': 'test form address',
        'email': 'form@prodtest.pl',
        'rating': 5,
        'notes': 'test notes',

    }
    inital_workdays = ProductionHouse.objects.count()
    response = client.post(url, data)
    assert response.status_code == 200
    assert ProductionHouse.objects.count() == inital_workdays
    storage = get_messages(response.wsgi_request)
    messages = [msg.message for msg in storage]
    assert len(messages) == 1
    assert messages[0] == 'NIP NUBER IS NOT CORRECT'


# ==================  EDIT  PRODUCTION HOUSE VIEW =============================


@pytest.mark.django_db
def test_production_house_edit_get_without_login(user_with_db, production_house_owner_user_with_db):
    client = Client()
    url = reverse('production-edit', args=[production_house_owner_user_with_db.pk])
    response = client.get(url, follow=True)
    assert response.status_code == 200
    redirect_chain = response.redirect_chain
    if redirect_chain:
        final_url, statushttp = redirect_chain[-1]
        assert final_url == f'/register_user/?next=/production-edit/{production_house_owner_user_with_db.pk}/'
        assert statushttp == 302


@pytest.mark.django_db
def test_production_house_edit_get_with_login(user_with_db, production_house_owner_user_with_db):
    client = Client()
    client.force_login(user_with_db[0])
    url = reverse('production-edit', args=[production_house_owner_user_with_db.pk])
    response = client.get(url)
    assert response.status_code == 200
    # ===== THROUGHT DJANGO FORM OBJECT PH IS INSTANCE ============
    production_form_instance = response.context['form'].instance
    print("production_form_instance:", production_form_instance)
    print("production_house_owner_user_with_db:", production_house_owner_user_with_db)
    assert production_form_instance == production_house_owner_user_with_db
    # ------- IN HTML ADDED VALUE TO PASS THIS TEST------------
    assert f'value="{production_house_owner_user_with_db.name}"' in response.content.decode('utf-8')


@pytest.mark.django_db
def test_production_house_edit_post_with_login(user_with_db, production_house_owner_user_with_db):
    client = Client()
    client.force_login(user_with_db[0])
    initial_name = ProductionHouse.objects.filter(user=user_with_db[0]).first().name
    initial_counter = ProductionHouse.objects.filter(user=user_with_db[0]).count()
    url = reverse('production-edit', args=[production_house_owner_user_with_db.pk])
    data = {
        'name': 'edited_production_house',
        'nip': 3758519109,
        'address': 'edited_addresss',
        'emial': 'edited@emial.com',
        'notes': 4,
    }
    response = client.post(url, data, follow=True)
    assert response.status_code == 200
    assert not initial_name == ProductionHouse.objects.filter(user=user_with_db[0]).first().name
    assert initial_counter == ProductionHouse.objects.filter(user=user_with_db[0]).count()


@pytest.mark.django_db
def test_production_house_edit_post_with_login_no_name(user_with_db, production_house_owner_user_with_db):
    client = Client()
    client.force_login(user_with_db[0])
    initial_name = ProductionHouse.objects.filter(user=user_with_db[0]).first().name
    initial_counter = ProductionHouse.objects.filter(user=user_with_db[0]).count()
    url = reverse('production-edit', args=[production_house_owner_user_with_db.pk])
    data = {
        'name': '',
        'nip': 3758519109,
        'address': 'edited_addresss',
        'emial': 'edited@emial.com',
        'notes': 4,
    }
    response = client.post(url, data, follow=True)
    assert response.status_code == 200
    storage = get_messages(response.wsgi_request)
    messages = [msg.message for msg in storage]
    assert len(messages) == 1
    assert messages[0] == 'NAME CANNOT BE EMPTY'
    assert initial_name == ProductionHouse.objects.filter(user=user_with_db[0]).first().name
    assert initial_counter == ProductionHouse.objects.filter(user=user_with_db[0]).count()


@pytest.mark.django_db
def test_production_house_edit_post_with_login_nip_too_short(user_with_db, production_house_owner_user_with_db):
    client = Client()
    client.force_login(user_with_db[0])
    initial_name = ProductionHouse.objects.filter(user=user_with_db[0]).first().name
    initial_counter = ProductionHouse.objects.filter(user=user_with_db[0]).count()
    url = reverse('production-edit', args=[production_house_owner_user_with_db.pk])
    data = {
        'name': 'edited_production_house',
        'nip': 37,
        'address': 'edited_addresss',
        'emial': 'edited@emial.com',
        'notes': 4,
    }
    response = client.post(url, data, follow=True)
    assert response.status_code == 200
    storage = get_messages(response.wsgi_request)
    messages = [msg.message for msg in storage]
    assert len(messages) == 1
    assert messages[0] == 'LENGTH OF NIP NUMBER IS NOT CORRECT'
    assert initial_name == ProductionHouse.objects.filter(user=user_with_db[0]).first().name
    assert initial_counter == ProductionHouse.objects.filter(user=user_with_db[0]).count()


@pytest.mark.django_db
def test_production_house_edit_post_with_login_nip_not_correct(user_with_db, production_house_owner_user_with_db):
    client = Client()
    client.force_login(user_with_db[0])
    initial_name = ProductionHouse.objects.filter(user=user_with_db[0]).first().name
    initial_counter = ProductionHouse.objects.filter(user=user_with_db[0]).count()
    url = reverse('production-edit', args=[production_house_owner_user_with_db.pk])
    data = {
        'name': 'edited_production_house',
        'nip': '1234567890',
        'address': 'edited_address',
        'emial': 'edited@emial.com',
        'notes': 4,
    }
    response = client.post(url, data, follow=True)
    assert response.status_code == 200
    storage = get_messages(response.wsgi_request)
    messages = [msg.message for msg in storage]
    assert len(messages) == 1
    assert messages[0] == 'NIP NUBER IS NOT CORRECT'
    assert initial_name == ProductionHouse.objects.filter(user=user_with_db[0]).first().name
    assert initial_counter == ProductionHouse.objects.filter(user=user_with_db[0]).count()


# ================== PRODUCTION HOUSE DELETE VIEW =============================


@pytest.mark.django_db
def test_production_house_delete_get_without_login(production_house_owner_user_with_db):
    client = Client()
    url = reverse('production-delete', args=[production_house_owner_user_with_db.pk])
    response = client.get(url, follow=True)
    assert response.status_code == 200
    redirect_chain = response.redirect_chain
    if redirect_chain:
        final_url, statushttp = redirect_chain[-1]
        assert final_url == f'/register_user/?next=/production-delete/{production_house_owner_user_with_db.pk}/'
        assert statushttp == 302


@pytest.mark.django_db
def test_production_delete_get_with_login(user_with_db, production_house_owner_user_with_db):
    client = Client()
    client.force_login(user_with_db[0])
    url = reverse('production-delete', args=[production_house_owner_user_with_db.pk])
    response = client.get(url, follow=True)
    assert response.status_code == 200
    assert response.context['productionhouse'] == production_house_owner_user_with_db


@pytest.mark.django_db
def test_productionhouse_delete_post_with_login_delete_no(user_with_db, production_house_owner_user_with_db):
    client = Client()
    client.force_login(user_with_db[0])
    url = reverse('production-delete', args=[production_house_owner_user_with_db.pk])
    data = {
        'action': 'NO',
    }
    initial_workday = ProductionHouse.objects.first()
    initial_count_workday = ProductionHouse.objects.count()
    response = client.post(url, data, follow=True)
    assert response.status_code == 200
    assert initial_workday == ProductionHouse.objects.first()
    assert initial_count_workday == ProductionHouse.objects.count()
    redirect_chain = response.redirect_chain
    if redirect_chain:
        final_url, statushttp = redirect_chain[-1]
        assert final_url == f'/productions-list/'
        assert statushttp == 302


@pytest.mark.django_db
def test_production_house_delete_post_with_login_delete_yes(production_house_owner_user_with_db):
    client = Client()
    client.force_login(production_house_owner_user_with_db.user)
    url = reverse('production-delete', args=[production_house_owner_user_with_db.pk])
    data = {
        'action': 'YES',
    }
    initial_workday = ProductionHouse.objects.first()
    initial_count_workday = ProductionHouse.objects.count()
    response = client.post(url, data, follow=True)
    assert response.status_code == 200
    assert not initial_workday == ProductionHouse.objects.first()
    assert ProductionHouse.objects.count() == initial_count_workday - 1
    redirect_chain = response.redirect_chain
    if redirect_chain:
        final_url, statushttp = redirect_chain[-1]
        assert final_url == f'/productions-list/'
        assert statushttp == 302


# =================================== CONTACTS ===========================
# =============================== CONTACTS LIST VIEW =================================

@pytest.mark.django_db
def test_contact_list_get_without_login(contact_db_owner_user_with_db):
    client = Client()
    url = reverse('contacts-list')
    response = client.get(url, follow=True)
    assert response.status_code == 200
    redirect_chain = response.redirect_chain
    if redirect_chain:
        final_url, statushttp = redirect_chain[-1]
        assert final_url == f'/register_user/?next=/contacts-list/'
        assert statushttp == 302


@pytest.mark.django_db
def test_contact_list_get_with_login(contact_db_owner_user_with_db):
    client = Client()
    client.force_login(contact_db_owner_user_with_db.user)
    url = reverse('contacts-list')
    response = client.get(url, follow=True)
    assert response.status_code == 200
    for contact in response.context['contacts']:
        assert contact.first_name == contact_db_owner_user_with_db.first_name


# ================================== CONTACTS ADD VIEW =============================


@pytest.mark.django_db
def test_contact_add_get_without_login(contact_db_owner_user_with_db):
    client = Client()
    url = reverse('contacts-add')
    response = client.get(url, follow=True)
    assert response.status_code == 200
    redirect_chain = response.redirect_chain
    if redirect_chain:
        final_url, statushttp = redirect_chain[-1]
        assert final_url == f'/register_user/?next=/contacts-add/'
        assert statushttp == 302


@pytest.mark.django_db
def test_contact_add_get_with_login(contact_db_owner_user_with_db):
    client = Client()
    client.force_login(contact_db_owner_user_with_db.user)
    url = reverse('contacts-add')
    response = client.get(url, follow=True)
    assert response.status_code == 200
    assert response.context['user'] == contact_db_owner_user_with_db.user


@pytest.mark.django_db
def test_contact_add_post_with_login(contact_db_owner_user_with_db):
    client = Client()
    client.force_login(contact_db_owner_user_with_db.user)
    url = reverse('contacts-add')
    initial_count = Contact.objects.filter(user=contact_db_owner_user_with_db.user).count()
    data = {
        'first_name': 'New_test_first_name',
        'last_name': 'Added_last_name',
        'occupation': 'Test_occupation',
        'email': 'test@pordhouse.pl',
        'phone': 3234442234,
        'notes': 'test notes',
    }
    response = client.post(url, data, follow=True)
    assert response.status_code == 200
    assert Contact.objects.filter(user=contact_db_owner_user_with_db.user).count() == initial_count + 1


@pytest.mark.django_db
def test_contact_add_post_with_login_no_name(contact_db_owner_user_with_db):
    client = Client()
    client.force_login(contact_db_owner_user_with_db.user)
    url = reverse('contacts-add')
    initial_count = Contact.objects.filter(user=contact_db_owner_user_with_db.user).count()
    data = {
        'first_name': '',
        'last_name': 'Added_last_name',
        'occupation': 'Test_occupation',
        'email': 'test@pordhouse.pl',
        'phone': 3234442234,
        'notes': 'test notes',
    }
    response = client.post(url, data, follow=True)
    assert response.status_code == 200
    assert Contact.objects.filter(user=contact_db_owner_user_with_db.user).count() == initial_count
    storage = get_messages(response.wsgi_request)
    messages = [msg.message for msg in storage]
    assert len(messages) == 1
    assert messages[0] == "YOU DIDNT FILL FORM. CORRECTLY"


# =========================== CONTACT EDIT VIEW =============================

@pytest.mark.django_db
def test_contact_edit_get_without_login(contact_db_owner_user_with_db):
    client = Client()
    url = reverse('contacts-edit', args=[contact_db_owner_user_with_db.pk])
    response = client.get(url, follow=True)
    assert response.status_code == 200
    redirect_chain = response.redirect_chain
    if redirect_chain:
        final_url, statushttp = redirect_chain[-1]
        assert final_url == f'/register_user/?next=/contacts-edit/{contact_db_owner_user_with_db.pk}/'
        assert statushttp == 302


@pytest.mark.django_db
def test_contact_edit_get_with_login(contact_db_owner_user_with_db):
    client = Client()
    client.force_login(contact_db_owner_user_with_db.user)
    url = reverse('contacts-edit', args=[contact_db_owner_user_with_db.pk])
    response = client.get(url, follow=True)
    assert response.status_code == 200
    assert response.context['user'] == contact_db_owner_user_with_db.user
    contact_form_instance = response.context['form'].instance
    assert contact_form_instance == contact_db_owner_user_with_db


@pytest.mark.django_db
def test_contact_edit_post_with_login(contact_db_owner_user_with_db):
    client = Client()
    client.force_login(contact_db_owner_user_with_db.user)
    url = reverse('contacts-edit', args=[contact_db_owner_user_with_db.pk])
    data = {
        'first_name': 'EDITED_CONTACT_NAME',
    }
    response = client.post(url, data, follow=True)
    assert response.status_code == 200
    assert response.context['user'] == contact_db_owner_user_with_db.user
    assert Contact.objects.filter(user=contact_db_owner_user_with_db.user).first().first_name == data['first_name']


@pytest.mark.django_db
def test_contact_edit_post_with_login(contact_db_owner_user_with_db):
    client = Client()
    client.force_login(contact_db_owner_user_with_db.user)
    url = reverse('contacts-edit', args=[contact_db_owner_user_with_db.pk])
    data = {
        'first_name': '',
    }
    response = client.post(url, data, follow=True)
    assert response.status_code == 200
    assert response.context['user'] == contact_db_owner_user_with_db.user
    assert not Contact.objects.filter(user=contact_db_owner_user_with_db.user).first().first_name == data['first_name']
    storage = get_messages(response.wsgi_request)
    messages = [msg.message for msg in storage]
    assert len(messages) == 1
    assert messages[0] == "YOU DIDNT FILL FORM. CORRECTLY"


# ================== CONTACT DELETE VIEW =============================


@pytest.mark.django_db
def test_contact_delete_get_without_login(contact_db_owner_user_with_db):
    client = Client()
    url = reverse('contacts-delete', args=[contact_db_owner_user_with_db.pk])
    response = client.get(url, follow=True)
    assert response.status_code == 200
    redirect_chain = response.redirect_chain
    if redirect_chain:
        final_url, statushttp = redirect_chain[-1]
        assert final_url == f'/register_user/?next=/contacts-delete/{contact_db_owner_user_with_db.pk}/'
        assert statushttp == 302


@pytest.mark.django_db
def test_contact_delete_get_with_login(contact_db_owner_user_with_db):
    client = Client()
    client.force_login(contact_db_owner_user_with_db.user)
    url = reverse('contacts-delete', args=[contact_db_owner_user_with_db.pk])
    response = client.get(url, follow=True)
    assert response.status_code == 200
    assert response.context['contact'] == contact_db_owner_user_with_db


@pytest.mark.django_db
def test_contacts_delete_post_with_login_delete_no(contact_db_owner_user_with_db):
    client = Client()
    client.force_login(contact_db_owner_user_with_db.user)
    url = reverse('contacts-delete', args=[contact_db_owner_user_with_db.pk])
    data = {
        'action': 'NO',
    }
    initial_workday = Contact.objects.first()
    initial_count_workday = Contact.objects.count()
    response = client.post(url, data, follow=True)
    assert response.status_code == 200
    assert initial_workday == Contact.objects.first()
    assert initial_count_workday == Contact.objects.count()
    redirect_chain = response.redirect_chain
    if redirect_chain:
        final_url, statushttp = redirect_chain[-1]
        assert final_url == f'/contacts-list/'
        assert statushttp == 302


@pytest.mark.django_db
def test_contacts_delete_post_with_login_delete_yes(contact_db_owner_user_with_db):
    client = Client()
    client.force_login(contact_db_owner_user_with_db.user)
    url = reverse('contacts-delete', args=[contact_db_owner_user_with_db.pk])
    data = {
        'action': 'YES',
    }
    initial_workday = Contact.objects.first()
    initial_count_workday = Contact.objects.count()
    response = client.post(url, data, follow=True)
    assert response.status_code == 200
    assert not initial_workday == Contact.objects.first()
    assert Contact.objects.count() == initial_count_workday - 1
    redirect_chain = response.redirect_chain
    if redirect_chain:
        final_url, statushttp = redirect_chain[-1]
        assert final_url == f'/contacts-list/'
        assert statushttp == 302

# ==============================  SELENIUM TEST =======================
# class SeleniumTest(LiveServerTestCase):
#     def setUp(self):
#         self.user_db = User.objects.create_user(username='test', password='test123pytest')
#         self.project = Project.objects.create(name='test_project', daily_rate=1200, type_of_overhours='10',
#                                               user_id=self.user_db.id)
#         self.workday = WorkDay.objects.create(id=37, date='2024-03-17', amount_of_overhours=0,
#                                               type_of_workday="shooting day", project_id=self.project.id,
#                                               last_updated='2024-03-05 07:53:27.834922 +00:00')
#
#     def tearDown(self):
#         self.driver.quit()
#
#     def test_project_list_add_days_button_exist(self):
#         self.driver = webdriver.Chrome()
#         self.driver.maximize_window()
#         self.username = 'test'
#         self.password = 'test123pytest'
#         self.driver.get(self.live_server_url + '/login_user/')
#         username_field = self.driver.find_element(By.NAME, 'username')
#         password_field = self.driver.find_element(By.NAME, 'password')
#         username_field.send_keys(self.username)
#         password_field.send_keys(self.password)
#         login_button = self.driver.find_element(By.ID, 'loginbtn')
#         login_button.click()
#         WebDriverWait(self.driver, 2)
#         self.driver.get(self.live_server_url + "/project-list/")
#         add_days_button = WebDriverWait(self.driver, 2).until(
#             expected_conditions.element_to_be_clickable((By.ID, "add_days"))
#         )
#         add_days_button.click()
#         current_url = self.driver.current_url
#         expected_url = self.live_server_url + "/project/days/1/"
#         assert current_url == expected_url
