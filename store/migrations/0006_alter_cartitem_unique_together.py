# Generated by Django 5.2 on 2025-05-19 08:19

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('store', '0005_alter_cartitem_product'),
    ]

    operations = [
        migrations.AlterUniqueTogether(
            name='cartitem',
            unique_together=set(),
        ),
    ]
