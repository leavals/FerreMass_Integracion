# Generated by Django 5.0.6 on 2024-05-29 03:17

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0005_product_marca'),
    ]

    operations = [
        migrations.AddField(
            model_name='payment',
            name='detalles',
            field=models.TextField(blank=True, null=True),
        ),
    ]
