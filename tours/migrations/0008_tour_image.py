# Generated by Django 3.2.6 on 2021-09-05 01:48

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('tours', '0007_auto_20210818_0856'),
    ]

    operations = [
        migrations.AddField(
            model_name='tour',
            name='image',
            field=models.ImageField(default=None, upload_to='images/tours/%Y/%m'),
        ),
    ]
