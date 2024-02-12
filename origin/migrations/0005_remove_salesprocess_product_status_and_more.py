# Generated by Django 5.0.2 on 2024-02-12 08:58

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('origin', '0004_salesprocess_product_status_and_more'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='salesprocess',
            name='product_status',
        ),
        migrations.RemoveField(
            model_name='salesprocess',
            name='sales_representative',
        ),
        migrations.AlterField(
            model_name='salesperformance',
            name='closed_deals_count',
            field=models.IntegerField(),
        ),
    ]
