# Generated by Django 3.0.8 on 2020-09-16 06:03

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('messaging', '0010_message_id_on_client'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='message',
            name='image',
        ),
        migrations.AddField(
            model_name='message',
            name='file',
            field=models.FileField(blank=True, null=True, upload_to='tombug'),
        ),
    ]