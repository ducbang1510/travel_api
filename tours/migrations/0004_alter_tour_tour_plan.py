# Generated by Django 3.2.6 on 2021-08-11 02:47

import ckeditor.fields
from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('tours', '0003_auto_20210810_1629'),
    ]

    operations = [
        migrations.AlterField(
            model_name='tour',
            name='tour_plan',
            field=ckeditor.fields.RichTextField(default=None, null=True),
        ),
    ]
