from django.db import models
import re


# Create your models here.
class Worker(models.Model):
    first_Name = models.CharField(max_length=128)
    last_Name = models.CharField(max_length=128)
    occupation = models.CharField(max_length=56)
    email = models.EmailField()
    phone = models.IntegerField()
    notes = models.TextField(null=True)


class ProductionHouse(models.Model):
    RATING_CHOICES = [
        (1, 'Słaby'),
        (2, 'Przeciętny'),
        (3, 'Dobry'),
        (4, 'Bardzo dobry'),
        (5, 'Doskonały'),
    ]
    name = models.CharField(max_length=128)
    nip = models.IntegerField()
    address = models.CharField(max_length=256)
    email = models.EmailField()
    workers = models.ManyToManyField(Worker)
    rating = models.IntegerField(choices=RATING_CHOICES)
    notes = models.TextField(null=True)


class Project(models.Model):
    name = models.CharField(max_length=128)
    date_created = models.DateTimeField(auto_now_add=True)
    daily_rate = models.IntegerField()
    type_of_overhours = models.CharField(max_length=32)
    production = models.ForeignKey(ProductionHouse, on_delete=models.CASCADE, null=True)
    notes = models.TextField(null=True)
    occupation = models.CharField(max_length=56)

# USUWANIE TEKSTU Z TYPE OF SHOOTING DAY
def just_numb(value):
    return re.sub(r'[^0-9]', '', value)


class DayOfWork(models.Model):
    date = models.DateField()
    amount_of_overhours = models.IntegerField()
    earnings = models.IntegerField(blank=True, null=True)
    type_of_workday = models.CharField(max_length=36)
    notes = models.TextField()
    project = models.ForeignKey(Project, on_delete=models.CASCADE, blank=True, null=True)

    def calculate_earnings(self):
        if self.amount_of_overhours != '0':
            # ZAROBKI DLA WYBRANEGO TYPU DNIA PRACY wraz z wybranym procentowo
            if self.type_of_workday == 'shoot_day':
                self.earnings = int(self.amount_of_overhours) * (
                        self.project.daily_rate * (int(self.project.type_of_overhours) / 100)) + self.project.daily_rate
            elif self.type_of_workday == 'rehersal':
                self.earnings = (int(self.amount_of_overhours) * (
                        self.project.daily_rate * (
                        int(self.project.type_of_overhours) / 100)) + self.project.daily_rate) / 2
            elif self.type_of_workday == 'transport':
                self.earnings = (int(self.amount_of_overhours) * (
                        self.project.daily_rate * (
                        int(self.project.type_of_overhours) / 100)) + self.project.daily_rate) / 2
            else:
                self.earnings = (int(self.amount_of_overhours) * (
                        self.project.daily_rate * (
                        int(self.project.type_of_overhours) / 100)) + self.project.daily_rate) * (
                                        int(just_numb(self.type_of_workday)) / 100)
        else:
            if self.type_of_workday == 'shoot_day':
                self.earnings = self.project.daily_rate
            elif self.type_of_workday == 'rehersal':
                self.earnings = self.project.daily_rate / 2
            elif self.type_of_workday == 'rehersal':
                self.earnings = self.project.daily_rate / 2
            else:

                self.earnings = self.project.daily_rate * (int(just_numb(self.type_of_workday)) / 100)

        self.save()
