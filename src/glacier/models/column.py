from dataclasses import dataclass
from typing import Any, Optional


@dataclass
class Column:
    name: str
    default: Optional[Any] = None
    is_identifier: Optional[bool] = False
