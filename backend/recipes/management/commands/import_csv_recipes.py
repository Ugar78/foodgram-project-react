import csv

from django.core.management.base import BaseCommand

from foodgram.settings import BASE_DIR
from recipes.models import IngredientsRecipe, Recipe, TagsRecipe


class Command(BaseCommand):

    def import_recipes(self):
        file_path = BASE_DIR.parent / 'data/recipes.csv'
        with open(
            file_path,
            encoding='utf-8'
        ) as csvfile:
            reader = csv.DictReader(csvfile)
            id_s = 1
            for row in reader:
                Recipe.objects.create(
                    id=id_s,
                    name=row['name'],
                    cooking_time=row['cooking_time'],
                    text=row['text'],
                    image=row['image'],
                    created_at=row['created_at'],
                    author_id=row['author_id'],
                )
                id_s += 1

    def import_ingredients_recipes(self):
        file_path = BASE_DIR.parent / 'data/ingredients_recipes.csv'
        with open(
            file_path,
            encoding='utf-8'
        ) as csvfile:
            reader = csv.DictReader(csvfile)
            id_s = 1
            for row in reader:
                IngredientsRecipe.objects.create(
                    id=id_s,
                    amount=row['amount'],
                    ingredients_id=row['ingredients_id'],
                    recipe_id=row['recipe_id'],
                )
                id_s += 1

    def import_tags_recipes(self):
        file_path = BASE_DIR.parent / 'data/tags_recipes.csv'
        with open(
            file_path,
            encoding='utf-8'
        ) as csvfile:
            reader = csv.DictReader(csvfile)
            id_s = 1
            for row in reader:
                TagsRecipe.objects.create(
                    id=id_s,
                    recipe_id=row['recipe_id'],
                    tags_id=row['tags_id'],
                )
                id_s += 1

    def handle(self, *args, **options):
        self.import_recipes()
        self.import_ingredients_recipes()
        self.import_tags_recipes()
        self.stdout.write(self.style.SUCCESS('Data imported successfully'))
