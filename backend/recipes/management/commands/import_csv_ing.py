import csv

from django.core.management.base import BaseCommand

from foodgram.settings import BASE_DIR
from recipes.models import Ingredients


class Command(BaseCommand):
    def import_ingredients(self):
        file_path = BASE_DIR.parent / 'data/ingredients.csv'
        with open(
            file_path,
            encoding='utf-8'
        ) as csvfile:
            reader = csv.DictReader(csvfile)
            id_ing = 1
            for row in reader:
                Ingredients.objects.create(
                    id=id_ing,
                    name=row['name'],
                    measurement_unit=row['measurement_unit'],
                )
                id_ing += 1

    def handle(self, *args, **options):
        self.import_ingredients()
        self.stdout.write(self.style.SUCCESS('Data imported successfully'))
