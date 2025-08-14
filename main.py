import asyncio
import logging
from src.services.parser_service import ParserService


def setup_logging():
    """Настройка логирования"""

    logging.basicConfig(
        level = logging.INFO,
        format = '%(asctime)s - %(levelname)s - %(message)s',
        handlers = [
            logging.StreamHandler()
        ]
    )

async def main():
    """Главная функция для запуска парсинга"""

    setup_logging()

    parser_service = ParserService()

    # Запуск парсинга всех категорий
    await parser_service.start_parsing('https://alecomp.ru/')


if __name__ == "__main__":

    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("Парсинг прерван пользователем")
        logging.warning("Парсинг прерван пользователем")
    except Exception as e:
        print(f"Критическая ошибка: {e}")
        logging.error(f"Критическая ошибка в main: {e}")