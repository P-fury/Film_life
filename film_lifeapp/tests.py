from django.test import TestCase
from film_lifeapp.functions import nip_checker
import pytest


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
