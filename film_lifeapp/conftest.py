import pytest
from django.contrib.auth.models import User
from selenium import webdriver
from selenium.webdriver.common.by import By

from film_lifeapp.models import WorkDay, Project, ProductionHouse, Contact


@pytest.fixture
def user():
    return User.objects.create_user(username='test', password='<PASSWORD>')


@pytest.fixture
def user_with_db():
    user_db = User.objects.create_user(username='test', password='test123pytest')
    project = Project.objects.create(name='test_project', daily_rate=1200, type_of_overhours='10', user_id=user_db.id)
    workday = WorkDay.objects.create(date='2024-03-17', amount_of_overhours=0,
                                     type_of_workday="shooting day", project_id=project.id,
                                     last_updated='2024-03-05 07:53:27.834922 +00:00')
    workday.calculate_earnings()
    project.update_total_earnings()
    return user_db, project, workday


@pytest.fixture()
def work_day():
    return WorkDay.objects.create(id=37, date='2024-03-17', amount_of_overhours='0', earnings=1100,
                                  type_of_workday="shooting day", project_id=1,
                                  last_updated='2024-03-05 07:53:27.834922 +00:00'
                                  )


@pytest.fixture()
def project_test():
    return Project.objects.create(name='test_project', daily_rate=1200, type_of_overhours=10)


@pytest.fixture()
def project_add_form():
    data = {
        'name': 'test_project',
        'daily_rate': 1000,
        'type_of_overhours': 10,
    }
    return data


@pytest.fixture()
def workday_add_form():
    data = {
        'date': '2021-03-17',
        'overhours': 0,
        'type_of_day': 'shooting day',
        'notes': '',
        'percent_of_daily': '',
    }
    return data


@pytest.fixture()
def project_edit_form():
    data = {
        'name': 'edited_project',
        'daily_rate': 100,
        'type_of_overhours': 14
    }
    return data


@pytest.fixture()
def production_house_db():
    prod_house = ProductionHouse.objects.create(name='test_production_house', nip='5213560300',
                                                address='test address', email='test@pordhouse.pl',
                                                rating=4, notes='test notes')
    return prod_house


@pytest.fixture()
def production_house_owner_user_with_db(user_with_db):
    prod_house = ProductionHouse.objects.create(name='test_production_house', nip='5213560300',
                                                address='test address', email='test@pordhouse.pl',
                                                rating=4, notes='test notes', user=user_with_db[0])
    return prod_house


@pytest.fixture()
def production_house_add_form_owner_user_with_db(user_with_db):
    data = {
        'name': 'test_form_production_house',
        'nip': '9512354036',
        'address': 'test form address',
        'email': 'form@prodtest.pl',
        'rating': 5,
        'notes': 'test notes',

    }
    return data


@pytest.fixture()
def contact_db_owner_user_with_db(user_with_db, production_house_owner_user_with_db):
    contact = Contact.objects.create(first_name='Test_name', last_name='Test_last_name', occupation='Test_occupation',
                                     email='test@pordhouse.pl',
                                     phone=3234442234, notes='test notes', user=user_with_db[0])
    contact.production_house.add(production_house_owner_user_with_db)
    return contact


@pytest.fixture()
def selenium_auto_login(user):
    driver = webdriver.Chrome()
    driver.maximize_window()
    username = 'test'
    password = '<PASSWORD>'
    driver.get('http://localhost:8000/login_user/')
    username_field = driver.find_element(By.NAME, 'username')
    password_field = driver.find_element(By.NAME, 'password')
    username_field.send_keys(username)
    password_field.send_keys(password)
    login_button = driver.find_element(By.ID, 'loginbtn')
    login_button.click()
