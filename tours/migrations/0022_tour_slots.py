# Generated by Django 3.2.7 on 2021-10-10 02:04

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('tours', '0021_rename_status_invoice_status_payment'),
    ]

    operations = [
        migrations.AddField(
            model_name='tour',
            name='slots',
            field=models.IntegerField(default=0, null=True),
        ),
    ]
