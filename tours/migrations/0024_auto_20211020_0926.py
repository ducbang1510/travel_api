# Generated by Django 3.2.7 on 2021-10-20 02:26

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('tours', '0023_tour_banner'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='blog',
            options={'ordering': ['-id']},
        ),
        migrations.AlterModelOptions(
            name='comment',
            options={'ordering': ['-id']},
        ),
        migrations.AlterModelOptions(
            name='customer',
            options={'ordering': ['-id']},
        ),
        migrations.AlterModelOptions(
            name='invoice',
            options={'ordering': ['-id']},
        ),
        migrations.AlterModelOptions(
            name='payer',
            options={'ordering': ['-id']},
        ),
        migrations.AlterModelOptions(
            name='tourimage',
            options={'ordering': ['-id']},
        ),
    ]
