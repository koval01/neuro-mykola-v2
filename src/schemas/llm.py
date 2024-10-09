from typing import TypedDict, Optional


class Answer(TypedDict):
    reply_to: Optional[str]
    text: str

class ResponseSchema(TypedDict):
    answers: list[Answer]
    skip: Optional[bool]
