# Generated by Django 5.0.3 on 2024-04-01 10:31

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('film_lifeapp', '0005_alter_startstop_time_diff'),
    ]

    operations = [
        migrations.AlterField(
            model_name='project',
            name='occupation',
            field=models.CharField(blank=True, max_length=56, null=True),
        ),
    ]
