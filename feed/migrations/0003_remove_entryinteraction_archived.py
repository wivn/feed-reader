# Generated by Django 3.0.2 on 2020-07-21 02:21

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('feed', '0002_feedlessentry'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='entryinteraction',
            name='archived',
        ),
    ]
