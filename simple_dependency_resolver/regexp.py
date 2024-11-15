import re

from simple_dependency_resolver.const import SPECIAL_TYPES

special_type_pattern = re.compile(r'\b(' + '|'.join(SPECIAL_TYPES) + r')\b')