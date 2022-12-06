from __future__ import annotations
from typing import List, Optional
from pydantic import BaseModel


class InitMessage(BaseModel):
    reservation_id: str
    srn_blacklist: Optional[List[str]]