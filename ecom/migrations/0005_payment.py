# Generated by Django 3.0.5 on 2023-06-06 09:43

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('ecom', '0004_auto_20230518_1731'),
    ]

    operations = [
        migrations.CreateModel(
            name='Payment',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('transaction_id', models.PositiveIntegerField(unique=True)),
                ('amount', models.PositiveIntegerField()),
                ('status', models.CharField(choices=[('SUCCESS', 'Success'), ('PENDING', 'Pending'), ('FAILED', 'Failed'), ('DECLINED', 'Declined')], max_length=10)),
                ('timestamp', models.DateTimeField(auto_now_add=True)),
                ('customer', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='ecom.Customer')),
                ('product', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='ecom.Product')),
            ],
        ),
    ]
