# Generated by Django 3.0.8 on 2020-08-09 19:06

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('projects', '0015_auto_20200809_1905'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='project',
            name='portal',
        ),
    ]
