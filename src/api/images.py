from fastapi import APIRouter, UploadFile

from src.services.images import ImagesService

router = APIRouter(prefix="/images", tags=["Изображения отелей"])


@router.post("", summary="Загрузка изображения", description="<h1>Загрузите ваше изображение</h1>")
def upload_image(file: UploadFile):
    """
    Эндпоинт для загрузки изображения.

    Параметры:
    - file (UploadFile): Загружаемый файл изображения.

    Логика:
    - Передаёт файл в сервис `ImagesService.upload_image()`.
    - Файл сохраняется в директорию `src/static/images/`.

    Возвращает:
    - JSON: {"filename": "имя_файла", "status": "uploaded"}

    Примечание:
    - Для асинхронной обработки (например, изменение размера) рекомендуется использовать `BackgroundTasks`.
    """
    ImagesService().upload_image(file)

    # from fastapi import APIRouter, UploadFile, BackgroundTasks
    # def upload_image(file: UploadFile, background_tasks: BackgroundTasks)
    # background_tasks.add_task(resize_image, image_path)
    # return {"message": "Изображение загружено"}
