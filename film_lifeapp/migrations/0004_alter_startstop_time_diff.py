# Generated by Django 5.0.3 on 2024-03-28 13:24

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('film_lifeapp', '0003_startstop_time_diff'),
    ]

    operations = [
        migrations.AlterField(
            model_name='startstop',
            name='time_diff',
            field=models.TimeField(blank=True, null=True),
        ),
    ]
