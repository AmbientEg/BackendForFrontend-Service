"""Navigation response adapter for mobile clients.

Phase-1: Return response as-is from navigation service.
TODO(phase-2): Add mobile optimization.
"""

import logging
from typing import Any, Dict

logger = logging.getLogger(__name__)


class NavigationAdapter:
    @staticmethod
    def adapt_route(service_response: Dict[str, Any]) -> Dict[str, Any]:
        return service_response
