from typing import List
from urllib.parse  import urljoin
import logging

from bs4 import BeautifulSoup

from src.core.settings import settings
from src.scrapers.scraper import PageScraper


logger = logging.getLogger(__name__)


class StartPageParser:
    """Парсер категорий товаров"""

    def __init__(self):
        self.scraper = PageScraper()

    async def get_categories(self, url: str) -> List[str]:
        """Извлекает ссылки категорий товаров"""

        logger.info(f"Получение категорий с: {url}")

        html = await self.scraper.scrape_page(url)
        soup = BeautifulSoup(html, "html.parser")

        initial_categories = []

        # Извлечение основных категорий с главной страницы
        category_blocks = soup.find_all('li', class_ = 'ty-menu__item cm-menu-item-responsive dropdown-vertical__dir menu-level-')
        for block in category_blocks:
            links = block.find_all('a', href = True)
            for link in links:
                href = link.get('href')
                if href:
                    initial_categories.append(href)
                    logger.debug(f"Найдена начальная категория: {href}")

        logger.info(f"Найдено начальных категорий: {len(initial_categories)}")

        final_categories = set()

        # Проверяем каждую категорию на наличие подкатегорий
        for category_url in initial_categories:
            logger.info(f"Проверяем категорию: {category_url}")

            category_html = await self.scraper.scrape_page(category_url)
            if not category_html:
                logger.warning(f"Не удалось получить HTML для: {category_url}")
                final_categories.add(category_url)
                continue

            category_soup = BeautifulSoup(category_html, "html.parser")

            # Проверяем наличие "subcategories clearfix"
            catalog_categories = category_soup.find('ul', class_ = 'subcategories clearfix')

            if catalog_categories:
                logger.info(f"Найден блок 'subcategories clearfix' в : {category_url}")
                # Извлекаем подкатегорию вместо основной категории
                links = catalog_categories.find_all('a', href = True)
                for link in links:
                    href = link.get('href')
                    if href:
                        final_categories.add(href)
                        logger.debug(f"Найдена подкатегория: {href}")
            else:
                # Если подкатегорий нет, оставляем основную категорию
                final_categories.add(category_url)
                logger.debug(f"Подкатегории не найдены, оставляем: {category_url}")

        logger.info(f"Итоговых категорий: {len(final_categories)}")

        return list(final_categories)