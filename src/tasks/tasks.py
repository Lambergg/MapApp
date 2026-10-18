import asyncio
import logging
import os

from fastapi_mail import FastMail, MessageSchema, MessageType
from PIL import Image
from pydantic import EmailStr

from src.mailconfig import conf
from src.tasks.celery_app import celery_instance

logger = logging.getLogger("tasks")


@celery_instance.task
def resize_image(image_path: str) -> None:
    """
    Изменяет размер изображения до заданной ширины (90px) и сохраняет в static.

    :param image_path: Полный путь к исходному изображению.
    :type image_path: Str
    :raises FileNotFoundError: Если файл изображения не найден.
    :raises Exception: При ошибках обработки изображения.
    """
    logger.debug(f"Вызываеться resize_image с аргументом {image_path=}")
    sizes = [90]
    output_folder = "src/static/images"

    # Открываем изображение
    img = Image.open(image_path)

    # Получаем имя файла и его расширение
    base_name = os.path.basename(image_path)
    name, ext = os.path.splitext(base_name)

    # Проходим по каждому размеру
    for size in sizes:
        # Сжимаем изображение
        img_resized = img.resize(
            (size, int(img.height * (size / img.width))),
            Image.Resampling.LANCZOS,
        )

        # Формируем имя нового файла
        new_file_name = f"{name}{ext}"

        # Полный путь для сохранения
        output_path = os.path.join(output_folder, new_file_name)

        # Сохраняем изображение
        img_resized.save(output_path)

    logger.info(
        f"Изображение сохранено в следующих размерах: {sizes} в папке {output_folder}"
    )


@celery_instance.task
def send_email(email: EmailStr, username: str, password: str) -> None:
    html_content = f"""
    <h3>Добро пожаловать в приложение "MapApp"!</h3>
    <p>Вы успешно зарегистрированы.</p>
    <p><b>Ваш логин:</b> {username}</p>
    <p><b>Ваш пароль:</b> {password}</p>
    <p>Пожалуйста, сохраните эти данные для входа.</p>
    """

    message = MessageSchema(
        subject="Ваши данные для входа",
        recipients=[email],  # type: ignore
        body=html_content,
        subtype=MessageType.html,
    )

    async def _send():
        fm = FastMail(conf)
        await fm.send_message(message)

    # Запускаем корутину в новом event loop внутри синхронной задачи
    asyncio.run(_send())
    logger.info("Пользователь создан. Письмо с данными отправляется.")
