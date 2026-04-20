import logging
from time import sleep
from PIL import Image
import os

from src.tasks.celery_app import celery_instance


@celery_instance.task
def test_task():
    """
    Пример фоновой задачи, имитирующей долгую операцию.

    Выполняет:
    - Паузу на 5 секунд.
    - Логирование завершения.

    Используется для демонстрации работы Celery.
    """
    logging.info("Я начал")
    sleep(5)
    logging.info("Я закончил")


@celery_instance.task
def resize_image(image_path: str):
    logging.debug(f"Вызываеться resize_image с аргументом {image_path=}")
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

    logging.info(
        f"Изображение сохранено в следующих размерах: {sizes} в папке {output_folder}"
    )
