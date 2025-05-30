import csv
import json
import os

from django.conf import settings
from django.core.management.base import BaseCommand

from recipes.models import Ingredient

DATA_DIR = os.path.join(settings.BASE_DIR, 'data')
JSON_FILE_PATH = os.path.join(DATA_DIR, 'ingredients.json')
CSV_FILE_PATH = os.path.join(DATA_DIR, 'ingredients.csv')


class Command(BaseCommand):
    help = 'Import ingredients data from JSON and CSV files'

    def handle(self, *args, **options):
        with open(JSON_FILE_PATH, 'r') as json_file:
            ingredients_json = json.load(json_file)
            for ingredient_data in ingredients_json:
                Ingredient.objects.get_or_create(
                    name=ingredient_data['name'],
                    measurement_unit=ingredient_data['measurement_unit']
                )

        with open(CSV_FILE_PATH, 'r') as csv_file:
            reader = csv.reader(csv_file)
            next(reader)
            for row in reader:
                Ingredient.objects.get_or_create(
                    name=row[0],
                    measurement_unit=row[1]
                )

        self.stdout.write(self.style.SUCCESS('Data imported successfully'))
