# Generated by Django 4.2 on 2023-06-28 06:25

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('api', '0026_pin'),
    ]

    operations = [
        migrations.AddField(
            model_name='userextra',
            name='email_confirmed',
            field=models.BooleanField(default=False),
        ),
    ]
