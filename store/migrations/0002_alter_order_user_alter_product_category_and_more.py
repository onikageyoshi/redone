# Generated by Django 5.1.3 on 2025-05-28 13:53

import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('store', '0001_initial'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.AlterField(
            model_name='order',
            name='user',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='orders', to=settings.AUTH_USER_MODEL),
        ),
        migrations.AlterField(
            model_name='product',
            name='category',
            field=models.CharField(choices=[('Fashion & Apparel', 'Fashion & Apparel'), ('Electronics', 'Electronics'), ('Home & Living', 'Home & Living'), ('Food & Beverages', 'Food & Beverages'), ('Beauty & Personal Care', 'Beauty & Personal Care'), ('Toys, Kids & Baby', 'Toys, Kids & Baby'), ('Tools & Hardware', 'Tools & Hardware'), ('Automotive', 'Automotive'), ('Sports & Outdoors', 'Sports & Outdoors'), ('Gaming', 'Gaming'), ('Books & Stationery', 'Books & Stationery')], default='Home & Living', max_length=40),
        ),
        migrations.AlterField(
            model_name='product',
            name='description',
            field=models.TextField(blank=True),
        ),
    ]
