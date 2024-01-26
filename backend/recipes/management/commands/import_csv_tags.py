import csv
from django.core.management.base import BaseCommand

from recipes.models import Tag
from foodgram.settings import BASE_DIR


class Command(BaseCommand):

    def import_tags(self):
        file_path = BASE_DIR.parent / 'data/tags.csv'
        with open(
            file_path,
            encoding='utf-8'
        ) as csvfile:
            reader = csv.DictReader(csvfile)
            id_s = 1
            for row in reader:
                Tag.objects.create(
                    id=id_s,
                    name=row['name'],
                    color=row['color'],
                    slug=row['slug'],
                )
                id_s += 1

    def handle(self, *args, **options):
        self.import_tags()
        self.stdout.write(self.style.SUCCESS('Data imported successfully'))
