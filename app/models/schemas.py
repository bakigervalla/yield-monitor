from pydantic import BaseModel, field_validator

from app.db.database import ALLOWED_PART_NUMBERS


class TestCreate(BaseModel):
    serial_number: str
    part_number: str
    status: bool

    @field_validator("serial_number")
    @classmethod
    def serial_not_empty(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("serial_number must not be empty")
        return v.strip()

    @field_validator("part_number")
    @classmethod
    def part_number_allowed(cls, v: str) -> str:
        if v not in ALLOWED_PART_NUMBERS:
            raise ValueError(f"part_number must be one of {ALLOWED_PART_NUMBERS}")
        return v


class Message(BaseModel):
    role: str
    content: str


class ChatRequest(BaseModel):
    question: str
    history: list[Message] = []
