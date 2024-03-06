from django.test import TestCase
from film_lifeapp.functions import nip_checker
import pytest
from django.urls import reverse
from django.test import Client

from film_lifeapp.models import Project


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


# --------------------------------------------------------------------


# ================== MAIN VIEW =============================
# class TestMainGet(TestCase):
#     def setUp(self):
#         self.project = Project.objects.create(name='test_project', id=1, daily_rate=1200)
@pytest.mark.django_db
def test_main_get_without_db():
    client = Client()
    url = reverse('main')
    response = client.get(url)
    assert response.status_code == 200


@pytest.mark.django_db
def test_main_get(day_of_work, project_test):
    client = Client()
    url = reverse('main')
    last_project = day_of_work
    response = client.get(url, {'last_project': last_project, 'project_id': project_test.id})
    assert response.status_code == 200
    assert response.context['last_project'] == last_project


# ================== PROJECT LIST VIEW =============================
@pytest.mark.django_db
def test_project_list_get_without_db():
    client = Client()
    url = reverse('project-list')
    response = client.get(url)
    assert response.status_code == 200


# ================== PROJECT ADD VIEW =============================
@pytest.mark.django_db
def test_project_list_get_without_db():
    client = Client()
    url = reverse('project-add')
    response = client.get(url)
    assert response.status_code == 200


# ================== PROJECT EDIT VIEW =============================

@pytest.mark.django_db
def test_project_edit_get_with_id(project_test):
    client = Client()
    url = reverse('project-edit', args=[project_test.id])
    response = client.get(url)
    assert response.status_code == 200

# sprawdzic 404 bez id i zle id