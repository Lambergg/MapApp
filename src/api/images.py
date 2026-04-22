from fastapi import APIRouter, UploadFile

from src.api.dependencies import UserRoleDep
from src.exceptions import AdminOrModeratorOrUserOnlyAccessHTTPException
from src.services.images import ImagesService

router = APIRouter(prefix="/images", tags=["Изображения отелей"])


@router.post(
    "/upload",
    summary="Загрузка изображения",
    description="<h1>Загрузите ваше изображение</h1>",
)
def upload_image(role: UserRoleDep, file: UploadFile):
    if role not in ("admin", "manager", "user"):
        raise AdminOrModeratorOrUserOnlyAccessHTTPException
    image_path = ImagesService().upload_image(file)
    image_url = image_path.replace("src/", "/")

    return {"image_url": image_url}
