# Generated by Django 3.0.5 on 2023-04-27 14:46

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('ecom', '0001_initial'),
    ]

    operations = [
        migrations.RenameModel(
            old_name='cart_item',
            new_name='CartItem',
        ),
    ]