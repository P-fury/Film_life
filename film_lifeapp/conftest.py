import pytest
from django.contrib.auth.models import User
from film_lifeapp.models import DayOfWork, Project, ProductionHouse


@pytest.fixture
def user():
    return User.objects.create_user(username='test', password='<PASSWORD>')


@pytest.fixture()
def day_of_work():
    return DayOfWork.objects.create(id=37, date='2024-03-17', amount_of_overhours='0', earnings=1100,
                                    type_of_workday="shoot_day", project_id=1,
                                    last_updated='2024-03-05 07:53:27.834922 +00:00'
                                    )


@pytest.fixture()
def project_test():
    return Project.objects.create(name='test_project', id=1, daily_rate=1200)
