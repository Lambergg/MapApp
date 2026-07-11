from pydantic import BaseModel


class BanAnswerDTO(BaseModel):
    """
    Схема для возврата сообщения о бане через API.
    """
    message: str

class ImageAnswerDTO(BaseModel):
    """
    Схема для возврата url изображения через API.
    """
    url: str