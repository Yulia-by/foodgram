from django.utils.translation import ugettext_lazy as _


MAX_LENGTH_USERNAME = 150
MAX_LENGTH_EMAIL = 254
MAX_LENGTH_FIRST_NAME = 150
MAX_LENGTH_LAST_NAME = 150
MAX_LENGTH_INGREDIENT_NAME = 128
MAX_LENGTH_MEASUREMENT_UNIT = 64
MAX_LENGTH_TAG_NAME = 32
MAX_LENGTH_SLUG_NAME = 32
MAX_LENGTH_RECIPE_NAME = 256
COOKING_TIME_MIN = 1
MESSAGE_COOKING_TIME = _('Время приготовления не может быть меньше минуты.')
MESSAGE_TAGS_UNIQUE = _('Теги не могут повторяться!')
MESSAGE_NOT_TAGS = _('Не указаны тэги')
INGREDIENT_NOT_FOUND = _('Указанный ингредиент не найден.')
MESSAGE_INGREDIENT_UNIQUE = _('Ингредиенты должны быть уникальными!')
MESSAGE_INGREDIENT_AMOUNT = _(
    'Количество ингредиента должно быть положительным числом.')
MESSAGE_AMOUNT = _('Количество должно быть равно хотя бы одному.')
INLINE_EXTRA = 0
INGREDIENT_AMOUNT_MIN = 1
MIN_NUM = 1
PAGE_SIZE = 6
MIN_HASH_GEN = 8
MAX_HASH_GEN = 10
MAX_HASH_LENGTH = 15
URL_MAX_LENGTH = 256
