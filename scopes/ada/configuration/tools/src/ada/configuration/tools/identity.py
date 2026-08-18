import re
import unicodedata

from ada.configuration.tools.errors import ToolConfigurationValidationError

_KEY_PATTERN = re.compile(r'^[a-z][a-z0-9_]*$')
_NON_KEY_PATTERN = re.compile(r'[^a-z0-9]+')


def build_identity_key(display_name: str) -> str:
    normalized = unicodedata.normalize('NFKD', display_name.strip())
    ascii_text = ''.join(
        character for character in normalized if not unicodedata.combining(character)
    )
    candidate = _NON_KEY_PATTERN.sub('_', ascii_text.casefold()).strip('_')
    if not candidate or not candidate[0].isalpha():
        raise ToolConfigurationValidationError('Generated identity key has an invalid format')
    if not _KEY_PATTERN.fullmatch(candidate):
        raise ToolConfigurationValidationError('Generated identity key has an invalid format')
    return candidate


def require_identity_key(value: str, *, label: str) -> str:
    normalized = value.strip().casefold()
    if not _KEY_PATTERN.fullmatch(normalized):
        raise ToolConfigurationValidationError(f'{label} has an invalid format')
    return normalized


def require_display_name(value: str, *, label: str) -> str:
    normalized = value.strip()
    if not normalized:
        raise ToolConfigurationValidationError(f'{label} must not be empty')
    return normalized
