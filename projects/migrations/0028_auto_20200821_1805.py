# Generated by Django 3.0.8 on 2020-08-21 18:05

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('projects', '0027_milestonecomment_created'),
    ]

    operations = [
        migrations.RenameField(
            model_name='milestonecomment',
            old_name='file',
            new_name='image',
        ),
    ]
