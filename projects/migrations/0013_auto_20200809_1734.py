# Generated by Django 3.0.8 on 2020-08-09 17:34

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('projects', '0012_auto_20200809_1729'),
    ]

    operations = [
        migrations.AlterField(
            model_name='project',
            name='portal',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='projects.Portal'),
        ),
    ]
