# Generated by Django 3.0.8 on 2020-08-22 07:52

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('projects', '0028_auto_20200821_1805'),
    ]

    operations = [
        migrations.AlterField(
            model_name='milestone',
            name='milestone',
            field=models.CharField(max_length=25),
        ),
    ]
