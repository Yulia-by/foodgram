import csv
import json
import os

from django.conf import settings
from django.core.management.base import BaseCommand

from recipes.models import Ingredient

DATA_DIR = os.path.join(settings.BASE_DIR, 'data')
JSON_FILE_PATH = os.path.join(DATA_DIR, 'ingredients.json')
CSV_FILE_PATH = os.path.join(DATA_DIR, 'ingredients.csv')


def load_ingredients(file_path):
    """Общая функция загрузки ингредиентов. """
    if file_path.suffix == '.json':
        with open(file_path, encoding='utf-8') as f:
            data = json.load(f)
            return [(item["name"], item["measurement_unit"]) for item in data]

    elif file_path.suffix == '.csv':
        with open(file_path, newline='', encoding='utf-8') as f:
            reader = csv.reader(f)
            next(reader)
            return list(reader)

    else:
        raise ValueError("Unsupported file format")


class Command(BaseCommand):
    help = 'Импортирование данных ингредиентов из JSON/CSV-файлов.'

    def handle(self, *args, **kwargs):
        try:
            ingredients_from_json = load_ingredients(JSON_FILE_PATH)
            ingredients_from_csv = load_ingredients(CSV_FILE_PATH)
            all_ingredients = set(ingredients_from_json + ingredients_from_csv)
            for name, unit in all_ingredients:
                Ingredient.objects.get_or_create(name=name,
                                                 measurement_unit=unit)

            self.stdout.write(self.style.SUCCESS(
                'Данные успешно импортированы'))

        except Exception as e:
            self.stderr.write(self.style.ERROR(str(e)))
