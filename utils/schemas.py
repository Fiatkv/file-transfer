from pydantic import BaseModel
from typing import Optional

from utils.constants import DEFAULT_SENDER

class TextPayload(BaseModel):
    text: str
    sender: Optional[str] = DEFAULT_SENDER