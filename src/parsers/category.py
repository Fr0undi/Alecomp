import re
import logging
from typing import List

from bs4 import BeautifulSoup

from src.scrapers.scraper import PageScraper

logger = logging.getLogger(__name__)


class CategoryPageParser:
    """Парсер ссылок на товары с детектором страниц ошибок"""

    def __init__(self):
        self.scraper = PageScraper()

    async def get_page_count(self, url: str) -> int:
        """Определяет количество страниц по детектору ошибок"""

        logger.debug(f"Определение количества страниц для: {url}")

        # Сначала смотрим на первую страницу
        html = await self.scraper.scrape_page(url)
        if not html:
            return 1

        soup = BeautifulSoup(html, 'html.parser')

        # Получаем товары с первой страницы для проверки
        first_page_products = self._extract_products_urls_from_soup(soup)
        if not first_page_products:
            logger.info("На первой странице товары не найдены")
            return 1

        # Ищем видимые номера страниц в пагинации
        page_numbers = []

        pattern = r'page-(\d+)'
        matches = re.findall(pattern, html)
        for match in matches:
            try:
                page_numbers.append(int(match))
            except ValueError:
                continue

        if page_numbers:
            visible_max = max(page_numbers)
            logger.debug(f"Максимальная видимая страница: page-{visible_max}")
        else:
            logger.info("Пагинация не найдена, возвращаем 1 страницу")
            return 1

        # Проверяем наличие кнопки следующего блока
        next_block_button = soup.find('div',
                                      class_='cm-history ty-pagination__item hidden-phone ty-pagination__range cm-ajax')

        # Ищем диапазоны вида "x - y"
        range_text = None
        range_elements = soup.find_all(string=re.compile(r'\d+\s*-\s*\d+'))
        for element in range_elements:
            match = re.search(r'(\d+)\s*-\s*(\d+)', element)
            if match:
                start, end = int(match.group(1)), int(match.group(2))
                # Проверяем, что это похоже на пагинацию
                if 1 <= start <= end <= 1000 and end > visible_max:
                    range_text = element
                    visible_max = max(visible_max, end)
                    logger.debug(f"Найден диапазон страниц: {element.strip()}")
                    break

        if not next_block_button and not range_text:
            # Если нет кнопки следующего блока и диапазонов - берем максимальную видимую
            total_pages = visible_max
            logger.info(f"Следующий блок страниц не найден. Всего страниц: {total_pages}")
            return total_pages

        # Если есть индикатор дополнительных страниц - ищем конец методом детектора ошибок
        logger.info("Найден индикатор дополнительных страниц, ищем конец по страницам ошибок")

        return await self._find_last_page_by_errors(url, visible_max)

    async def _find_last_page_by_errors(self, url: str, start_from: int) -> int:
        """Находит последнюю страницу по детектору страниц ошибок"""

        current_page = start_from + 1 # Номер проверяемой страницы
        last_valid_page = start_from # Номер последней подтвержденной валидной страницы
        consecutive_errors = 0 # Счётчик подряд идущих ошибок
        max_consecutive_errors = 3  # Лимит подряд идущих ошибок
        max_checks = 200  # Лимит количества проверенных страниц

        checks_made = 0 # Счётчик общего количества уже проверенных страниц
        base_url = url.rstrip('/')

        while current_page <= 300 and checks_made < max_checks and consecutive_errors < max_consecutive_errors:
            test_url = f"{base_url}/page-{current_page}/"
            logger.debug(f"Проверяем страницу page-{current_page}")

            try:
                test_html = await self.scraper.scrape_page(test_url)
                checks_made += 1

                if not test_html:
                    logger.debug(f"Страница page-{current_page} недоступна")
                    consecutive_errors += 1
                    current_page += 1
                    continue

                # Проверяем длину ответа
                if len(test_html) < 10000:
                    logger.debug(f"Страница page-{current_page} слишком короткая ({len(test_html)} символов)")
                    consecutive_errors += 1
                    current_page += 1
                    continue

                test_soup = BeautifulSoup(test_html, 'html.parser')

                # Основная проверка - является ли страница страницей ошибки
                if self._is_error_page(test_soup):
                    logger.debug(f"Страница page-{current_page} является страницей ошибки")
                    consecutive_errors += 1
                    current_page += 1
                    continue

                # Проверяем наличие товаров на странице
                current_page_products = self._extract_products_urls_from_soup(test_soup)

                if current_page_products:
                    # Есть товары - страница валидная
                    last_valid_page = current_page
                    consecutive_errors = 0  # Сбрасываем счетчик ошибок
                    logger.debug(f"Страница page-{current_page} содержит {len(current_page_products)} товаров")
                else:
                    # Нет товаров на странице - возможная ошибка
                    logger.debug(f"Страница page-{current_page} не содержит товаров")
                    consecutive_errors += 1

            except Exception as e:
                logger.error(f"Ошибка при проверке страницы page-{current_page}: {e}")
                consecutive_errors += 1

            current_page += 1

        if consecutive_errors >= max_consecutive_errors:
            logger.info(f"Остановлено после {consecutive_errors} подряд идущих ошибок")

        total_pages = last_valid_page
        logger.info(f"Найдено страниц: {total_pages} (до page-{last_valid_page})")
        return total_pages

    def _is_error_page(self, soup: BeautifulSoup) -> bool:
        """Проверяет, является ли страница страницей ошибки"""

        # Проверяем наличие блока ty-exception
        exception_block = soup.find('div', class_='ty-exception')
        if exception_block:
            logger.debug("Найден блок ty-exception => это страница ошибки")
            return True

        # Проверяем заголовок страницы
        title = soup.find('title')
        if title:
            title_text = title.get_text().strip().lower()
            error_titles = [
                'страница находится по новому адресу',
                'страница не найдена',
                '404',
                'not found',
                'ошибка'
            ]
            for error_title in error_titles:
                if error_title in title_text:
                    logger.debug(f"Ошибка в заголовке: '{title_text}'")
                    return True

        # Проверяем текст заголовка h1
        h1_title = soup.find('h1', class_='ty-exception__title')
        if h1_title:
            h1_text = h1_title.get_text().strip().lower()
            if any(phrase in h1_text for phrase in [
                'Страница товара переехала на новый адрес.',
                'страница товара переехала',
                'переехала на новый адрес',
                'не найдена'
            ]):
                logger.debug(f"Ошибка в H1: '{h1_text}'")
                return True

        # Проверяем meta robots на noindex (признак служебной страницы)
        meta_robots = soup.find('meta', attrs={'name': 'robots'})
        if meta_robots:
            content = meta_robots.get('content', '').lower()
            if 'noindex' in content:
                logger.debug("Найден meta robots noindex")
                return True

        # Проверяем отсутствие основного контента товаров
        product_blocks = soup.find_all('div', class_='ty-compact-list__title')
        if not product_blocks:
            # Дополнительно проверяем, что это именно ошибка, а не пустая категория
            page_text = soup.get_text().lower()
            error_phrases = [
                'переехала',
                'новому адресу',
                '404',
                'не найдена',
                'извините за неудобства'
            ]
            for phrase in error_phrases:
                if phrase in page_text:
                    logger.debug(f"Отсутствует контент товаров + найдена фраза ошибки: '{phrase}'")
                    return True

        return False

    def _extract_products_urls_from_soup(self, soup: BeautifulSoup) -> List[str]:
        """Извлекает список URL товаров из BeautifulSoup объекта"""

        product_links = set()
        item_blocks = soup.find_all('div', {'class': 'ty-compact-list__title'})

        for block in item_blocks:
            title_links = block.find_all('a')
            for link in title_links:
                href = link.get('href')
                if href:
                    product_links.add(href)
        return sorted(list(product_links))

    async def create_page_links(self, url: str) -> List[str]:
        """Создает ссылки на все страницы категории"""

        pages = []
        page_count = await self.get_page_count(url)

        logger.info(f"Создание ссылок для {page_count} страниц")

        base_url = url.rstrip('/')

        for page_number in range(1, page_count + 1):
            if page_number == 1:
                pages.append(url)
            else:
                pages.append(f"{base_url}/page-{page_number}/")

        logger.debug(f"Создано ссылок на страницы: {len(pages)}")
        return pages

    async def get_product_links(self, url: str) -> List[str]:
        """Извлекает ссылки на товары со страницы категории"""

        logger.debug(f"Извлечение товаров с: {url}")

        html = await self.scraper.scrape_page(url)
        if not html:
            return []

        soup = BeautifulSoup(html, 'html.parser')

        # Проверяем, не является ли страница страницей ошибки
        if self._is_error_page(soup):
            logger.warning(f"Страница {url} является страницей ошибки, пропускаем")
            return []

        products_list = self._extract_products_urls_from_soup(soup)

        logger.info(f"Найдено товаров: {len(products_list)}")
        return products_list