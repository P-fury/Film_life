from datetime import datetime, timedelta
from django.contrib.auth.models import User
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.support import expected_conditions
from film_lifeapp.functions import nip_checker
import pytest
from django.urls import reverse
from django.test import Client
from film_lifeapp.models import StartStop, Project, WorkDay
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


# ================== PROJECT LIST VIEW =============================
@pytest.mark.django_db
def test_project_list_get_without_db():
    client = Client()
    url = reverse('project-list')
    response = client.get(url, follow=True)
    assert response.status_code == 200
    redirect_chain = response.redirect_chain
    if redirect_chain:
        final_url, statushttp = redirect_chain[-1]
        assert final_url == "register"
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


# ================== PROJECT ADD VIEW =============================
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


# ================== PROJECT ADD DAYS VIEW =============================


# ================== PROJECT EDIT VIEW =============================

@pytest.mark.django_db
def test_project_edit_get_with_id(project_test):
    client = Client()
    url = reverse('project-edit', args=[project_test.id])
    response = client.get(url, follow=True)
    assert response.status_code == 404


# sprawdzic 404 bez id i zle id

#==============================  SELENIUM TEST =======================
# class YourTestCase(LiveServerTestCase):
#     def setUp(self):
#         self.user_db = User.objects.create_user(username='test', password='test123pytest')
#         self.project = Project.objects.create(name='test_project', daily_rate=1200, type_of_overhours='10',
#                                               user_id=self.user_db.id)
#         self.workday = WorkDay.objects.create(id=37, date='2024-03-17', amount_of_overhours=0,
#                                               type_of_workday="shoot_day", project_id=self.project.id,
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
