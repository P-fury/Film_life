import pytest
from django.contrib.auth.models import User
from selenium import webdriver
from selenium.webdriver.common.by import By

from film_lifeapp.models import WorkDay, Project, ProductionHouse


@pytest.fixture
def user():
    return User.objects.create_user(username='test', password='<PASSWORD>')


@pytest.fixture
def user_with_db():
    user_db = User.objects.create_user(username='test', password='test123pytest')
    project = Project.objects.create(name='test_project', daily_rate=1200, type_of_overhours='10', user_id=user_db.id)
    workday = WorkDay.objects.create(id=37, date='2024-03-17', amount_of_overhours=0,
                                     type_of_workday="shoot_day", project_id=project.id,
                                     last_updated='2024-03-05 07:53:27.834922 +00:00')
    workday.calculate_earnings()
    project.update_total_earnings()
    return user_db, project, workday


@pytest.fixture()
def day_of_work():
    return WorkDay.objects.create(id=37, date='2024-03-17', amount_of_overhours='0', earnings=1100,
                                  type_of_workday="shoot_day", project_id=1,
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
def selenium_auto_login(user):
    driver = webdriver.Chrome()
    driver.maximize_window()
    username = 'test'
    password = '<PASSWORD>'
    driver.get('http://localhost:8000/login_user/')
    username_field = driver.find_element(By.NAME,'username')
    password_field = driver.find_element(By.NAME, 'password')
    username_field.send_keys(username)
    password_field.send_keys(password)
    login_button = driver.find_element(By.ID, 'loginbtn')
    login_button.click()