from django.conf import settings
from django.db import models
import re
from django.db.models import Sum
from django.db.models.signals import post_save
from django.dispatch import receiver

from film_lifeapp.functions import progresive_hours_counter


# Create your models here.


class ProductionHouse(models.Model):
    RATING_CHOICES = [
        (1, 'Weak'),
        (2, 'Average'),
        (3, 'Good'),
        (4, 'Very good'),
        (5, 'Excellent'),
    ]
    name = models.CharField(max_length=128)
    nip = models.BigIntegerField(blank=True, null=True)
    address = models.CharField(max_length=256, blank=True, null=True)
    email = models.EmailField(blank=True, null=True)
    rating = models.IntegerField(choices=RATING_CHOICES, blank=True, null=True, default=None)
    notes = models.TextField(blank=True, null=True)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, null=True)


class Contact(models.Model):
    first_name = models.CharField(max_length=128)
    last_name = models.CharField(max_length=128, blank=True, null=True, default=None)
    occupation = models.CharField(max_length=56, blank=True, null=True, default=None)
    production_house = models.ManyToManyField(ProductionHouse, blank=True, null=True, default=None)
    email = models.EmailField(blank=True, null=True, default=None)
    phone = models.BigIntegerField(blank=True, null=True, default=None)
    notes = models.TextField(blank=True, null=True, default=None)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)


class Project(models.Model):
    name = models.CharField(max_length=128)
    date_created = models.DateTimeField(auto_now_add=True)
    daily_rate = models.IntegerField()
    type_of_overhours = models.CharField(max_length=32)
    production_house = models.ForeignKey(ProductionHouse, on_delete=models.CASCADE, null=True)
    notes = models.TextField(default="", null=True)
    occupation = models.CharField(max_length=56, null=True)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, null=True)
    total_earnings_for_project = models.IntegerField(default=0)

    def update_total_earnings(self):
        total_earnings = self.workday_set.aggregate(total_earnings=Sum('earnings'))['total_earnings'] or 0
        self.total_earnings_for_project = total_earnings
        self.save()


# ================== DODAWANIE PODSUMOWANIA ZAROBKOW DO PROJEKTU ==============

def just_numb(value):
    return re.sub(r'[^0-9]', '', value)


class WorkDay(models.Model):
    date = models.DateField()
    amount_of_overhours = models.IntegerField()
    earnings = models.IntegerField(blank=True, null=True)
    type_of_workday = models.CharField(max_length=36)
    notes = models.TextField(null=True)
    project = models.ForeignKey(Project, on_delete=models.CASCADE, blank=True, null=True)
    last_updated = models.DateTimeField(auto_now=True, null=True, blank=True)

    def calculate_earnings(self):

        if self.project.type_of_overhours == 'progresive':
            if self.amount_of_overhours != '0':
                if self.type_of_workday == 'shooting day':
                    sum = progresive_hours_counter(self.project.daily_rate, self.amount_of_overhours)
                    self.earnings = sum
                elif self.type_of_workday == 'rehersal' or self.type_of_workday == 'transport':
                    sum = progresive_hours_counter(self.project.daily_rate, self.amount_of_overhours)
                    self.earnings = sum / 2
                else:
                    sum = progresive_hours_counter(self.project.daily_rate, self.amount_of_overhours)
                    self.earnings = sum * int(just_numb(self.type_of_workday)) / 100

            else:
                if self.type_of_workday == 'shooting day':
                    self.earnings = self.project.daily_rate
                elif self.type_of_workday == 'rehersal' or self.type_of_workday == 'transport':
                    self.earnings = self.project.daily_rate / 2
                else:
                    self.earnings = self.project.daily_rate * (int(just_numb(self.type_of_workday)) / 100)

        else:
            if self.amount_of_overhours != '0':
                # ZAROBKI DLA WYBRANEGO TYPU DNIA PRACY wraz z wybranym procentowo
                if self.type_of_workday == 'shooting day':
                    self.earnings = int(self.amount_of_overhours) * (
                            self.project.daily_rate * (
                            int(self.project.type_of_overhours) / 100)) + self.project.daily_rate
                elif self.type_of_workday == 'rehersal' or self.type_of_workday == 'transport':
                    self.earnings = (int(self.amount_of_overhours) * (
                            self.project.daily_rate * (
                            int(self.project.type_of_overhours) / 100)) + self.project.daily_rate) / 2
                else:
                    self.earnings = (int(self.amount_of_overhours) * (
                            self.project.daily_rate * (
                            int(self.project.type_of_overhours) / 100)) + self.project.daily_rate) * (
                                            int(just_numb(self.type_of_workday)) / 100)
            else:
                if self.type_of_workday == 'shooting day':
                    self.earnings = self.project.daily_rate
                elif self.type_of_workday == 'rehersal' or self.type_of_workday == 'transport':
                    self.earnings = self.project.daily_rate / 2
                else:
                    self.earnings = self.project.daily_rate * (int(just_numb(self.type_of_workday)) / 100)

        self.save()


@receiver(post_save, sender=WorkDay)
def update_project_total_earnings(sender, instance, **kwargs):
    if instance.project:
        instance.project.update_total_earnings()


class StartStop(models.Model):
    start_time = models.DateTimeField()
    end_time = models.DateTimeField(null=True, blank=True)
    duration = models.IntegerField(null=True, blank=True)
    project = models.ForeignKey(Project, on_delete=models.CASCADE, null=True, blank=True)
    time_diff = models.CharField(null=True, blank=True)