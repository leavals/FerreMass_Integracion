# Generated by Django 5.0.6 on 2024-05-29 03:27

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0006_payment_detalles'),
    ]

    operations = [
        migrations.AlterField(
            model_name='payment',
            name='confirmado',
            field=models.CharField(default='Por Pagar', max_length=20),
        ),
    ]
