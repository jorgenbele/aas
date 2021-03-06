# Generated by Django 2.2.12 on 2020-04-27 08:44

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion
import multiselectfield.db.fields


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='TimeSlot',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=40)),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='time_slots', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'ordering': ['name'],
            },
        ),
        migrations.CreateModel(
            name='NotificationProfile',
            fields=[
                ('time_slot', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, primary_key=True, related_name='notification_profile', serialize=False, to='aas_notoprofile.TimeSlot')),
                ('media', multiselectfield.db.fields.MultiSelectField(choices=[('EM', 'Email'), ('SM', 'SMS'), ('SL', 'Slack')], default='EM', max_length=8)),
                ('active', models.BooleanField(default=True)),
            ],
        ),
        migrations.CreateModel(
            name='TimeInterval',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('day', models.CharField(choices=[('MO', 'Monday'), ('TU', 'Tuesday'), ('WE', 'Wednesday'), ('TH', 'Thursday'), ('FR', 'Friday'), ('SA', 'Saturday'), ('SU', 'Sunday')], max_length=2)),
                ('start', models.TimeField(help_text='Local time.')),
                ('end', models.TimeField(help_text='Local time.')),
                ('time_slot', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='time_intervals', to='aas_notoprofile.TimeSlot')),
            ],
        ),
        migrations.CreateModel(
            name='Filter',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=40)),
                ('filter_string', models.TextField()),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='filters', to=settings.AUTH_USER_MODEL)),
            ],
        ),
        migrations.AddConstraint(
            model_name='timeslot',
            constraint=models.UniqueConstraint(fields=('name', 'user'), name='timeslot_unique_name_per_user'),
        ),
        migrations.AddField(
            model_name='notificationprofile',
            name='filters',
            field=models.ManyToManyField(related_name='notification_profiles', to='aas_notoprofile.Filter'),
        ),
        migrations.AddField(
            model_name='notificationprofile',
            name='user',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='notification_profiles', to=settings.AUTH_USER_MODEL),
        ),
        migrations.AddConstraint(
            model_name='filter',
            constraint=models.UniqueConstraint(fields=('name', 'user'), name='filter_unique_name_per_user'),
        ),
    ]
