from typing import Annotated

from fastapi import APIRouter, UploadFile, Depends

from src.api.dependencies import get_current_user_role
from src.services.images import ImagesService

router = APIRouter(prefix="/images", tags=["Изображения отелей"])


@router.post(
    "/upload",
    summary="Загрузка изображения",
    description="<h1>Загрузите ваше изображение</h1>",
)
def upload_image(role: Annotated[str, Depends(get_current_user_role)], file: UploadFile):
    """
    Загружает изображение на сервер.

    :param role: Роль текущего пользователя (для проверки прав доступа).
    :type role: Str
    :param file: Файл изображения, отправленный в формате multipart/form-data.
    :type file: UploadFile
    :return: URL загруженного изображения.
    :rtype: Dict[str, str]
    :raises AdminOrModeratorOrUserOnlyAccessHTTPException: Если роль не 'admin', 'moderator' или 'user'.
    """

    image_path = ImagesService().upload_image(file, role)
    image_url = image_path.replace("src/", "/")

    return {"image_url": image_url}
