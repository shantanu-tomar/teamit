# Generated by Django 3.0.8 on 2020-08-06 15:59

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='Member',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=20)),
                ('email', models.EmailField(max_length=254, unique=True)),
                ('role', models.CharField(choices=[('Administrator', 'Administrator'), ('Project Manager', 'Project Manager'), ('Developer', 'Developer'), ('Submitter', 'Submitter')], default='Submitter', max_length=16)),
                ('contact_number', models.CharField(blank=True, max_length=15, null=True)),
            ],
        ),
        migrations.CreateModel(
            name='Project',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('title', models.CharField(max_length=20)),
                ('description', models.TextField()),
                ('start_date', models.DateField()),
                ('end_date', models.DateField(blank=True, null=True)),
                ('status', models.CharField(choices=[('Active', 'Active'), ('In Progress', 'In Progress'), ('On Track', 'On Track'), ('Delayed', 'Delayed'), ('In Testing', 'In Testing'), ('On Hold', 'On Hold'), ('Approved', 'Approved'), ('Cancelled', 'Cancelled'), ('Planning', 'Planning'), ('Completed', 'Completed'), ('Invoiced', 'Invoiced')], default='Active', max_length=25)),
            ],
        ),
        migrations.CreateModel(
            name='Ticket',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('title', models.CharField(max_length=20)),
                ('description', models.TextField()),
                ('priority', models.CharField(choices=[('Bug/Error', 'Bug/Error'), ('Feature Request', 'Feature Request'), ('Other Comments', 'Other Comments'), ('Training/Document Requests', 'Training/Document Requests')], max_length=27)),
                ('status', models.CharField(choices=[('Open', 'Open'), ('Closed', 'Closed'), ('In Progress', 'In Progress'), ('Resolved', 'Resolved'), ('Additional Info Required', 'Additional Info Required')], max_length=24)),
                ('due_date', models.DateField(help_text='Deadline')),
                ('modified', models.DateField(auto_now=True)),
                ('created', models.DateField(auto_now_add=True)),
                ('assigned_to', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='assigned_to', to='projects.Member')),
                ('project', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='projects.Project')),
                ('submitter', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to='projects.Member')),
            ],
        ),
        migrations.CreateModel(
            name='TicketHistory',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('change', models.CharField(help_text='What changed ?', max_length=20)),
                ('old_value', models.CharField(blank=True, max_length=20, null=True)),
                ('new_value', models.CharField(blank=True, max_length=20, null=True)),
                ('date_changed', models.DateField(auto_now_add=True)),
                ('ticket', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='projects.Ticket')),
            ],
            options={
                'verbose_name_plural': 'Ticket History',
            },
        ),
    ]