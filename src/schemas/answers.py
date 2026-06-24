from pydantic import BaseModel


class BanAnswerDTO(BaseModel):
    """
    Схема для возврата сообщения о бане через API.
    """
    message: str