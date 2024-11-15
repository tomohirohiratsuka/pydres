import re

from pydres.const import SPECIAL_TYPES

special_type_pattern = re.compile(r'\b(' + '|'.join(SPECIAL_TYPES) + r')\b')