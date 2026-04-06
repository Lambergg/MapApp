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
    """
    Асинхронно изменяет размер изображения на несколько стандартных значений.

    Параметры:
    - image_path (str): Полный путь к исходному изображению.

    Логика:
    1. Открывает изображение с помощью PIL.
    2. Создаёт версии с шириной: 1000px, 500px, 200px.
    3. Сохраняет в `src/static/images` с суффиксом `_размерpx`.

    Особенности:
    - Сохраняет пропорции изображения.
    - Использует `LANCZOS` для высококачественного ресемплинга.

    Пример выходных файлов:
        original.jpg → original_1000px.jpg, original_500px.jpg, original_200px.jpg
    """
    logging.debug(f"Вызываеться resize_image с аргументом {image_path=}")
    sizes = [800, 500, 400, 320, 256, 200, 90]
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
            (size, int(img.height * (size / img.width))), Image.Resampling.LANCZOS
        )

        # Формируем имя нового файла
        new_file_name = f"{name}_{size}px{ext}"

        # Полный путь для сохранения
        output_path = os.path.join(output_folder, new_file_name)

        # Сохраняем изображение
        img_resized.save(output_path)

    logging.info(f"Изображение сохранено в следующих размерах: {sizes} в папке {output_folder}")
