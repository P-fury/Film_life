# Generated by Django 5.0.3 on 2024-03-28 14:20

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('film_lifeapp', '0004_alter_startstop_time_diff'),
    ]

    operations = [
        migrations.AlterField(
            model_name='startstop',
            name='time_diff',
            field=models.CharField(blank=True, null=True),
        ),
    ]
