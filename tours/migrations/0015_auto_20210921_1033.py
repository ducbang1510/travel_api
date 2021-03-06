# Generated by Django 3.2.6 on 2021-09-21 03:33

from django.db import migrations, models
import django.db.models.deletion
import phone_field.models


class Migration(migrations.Migration):

    dependencies = [
        ('tours', '0014_alter_customer_unique_together'),
    ]

    operations = [
        migrations.CreateModel(
            name='Payer',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=255)),
                ('email', models.EmailField(max_length=254)),
                ('phone', phone_field.models.PhoneField(blank=True, help_text='Contact phone number', max_length=31)),
                ('address', models.TextField(blank=True, null=True)),
            ],
        ),
        migrations.RemoveField(
            model_name='invoice',
            name='customers',
        ),
        migrations.AddField(
            model_name='customer',
            name='payer',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='customers', to='tours.payer'),
        ),
        migrations.AddField(
            model_name='invoice',
            name='payer',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='invoices', to='tours.payer'),
        ),
    ]
