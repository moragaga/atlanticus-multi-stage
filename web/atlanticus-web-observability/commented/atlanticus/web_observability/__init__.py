# Expone el contrato público mínimo de observabilidad web.
from atlanticus.web_observability.models import WebErrorInfo, WebEvent, WebSeverity
from atlanticus.web_observability.observability import WebObservability, configure_web_observability
from atlanticus.web_observability.sanitization import sanitize

__all__ = [
    'WebErrorInfo',
    'WebEvent',
    'WebObservability',
    'WebSeverity',
    'configure_web_observability',
    'sanitize',
]
