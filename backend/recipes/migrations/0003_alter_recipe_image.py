# Generated by Django 3.2.23 on 2024-01-28 12:34

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('recipes', '0002_initial'),
    ]

    operations = [
        migrations.AlterField(
            model_name='recipe',
            name='image',
            field=models.ImageField(default=None, null=True, upload_to='cats/images/', verbose_name='Фото'),
        ),
    ]