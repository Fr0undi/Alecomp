import re
import logging
from typing import List, Optional

from bs4 import BeautifulSoup

from src.scrapers.scraper import PageScraper
from src.schemas.product import Product, Supplier, SupplierOffer, PriceInfo, Attribute


logger = logging.getLogger(__name__)


class ProductPropertyParser:
    """Парсер для извлечения информации о товаре"""

    def __init__(self):
        self.scraper = PageScraper()

    async def parse_product(self, url: str) -> Optional[Product]:
        """Парсит страницу товара, возвращая объект Product"""

        logger.info(f"Парсинг товара: {url}")

        html = await self.scraper.scrape_page(url)
        if not html:
            logger.error(f"Не удалось получить HTML: {url}")
            return None

        soup = BeautifulSoup(html, "html.parser")

        # Извлекаем основную информацию о товаре
        title = self._extract_title(soup)
        description = self._extract_description(soup)
        article = self._extract_article(soup)
        brand = self._extract_brand(soup)
        country_of_origin = self._extract_country(soup)
        warranty_months = self._extract_warranty_months(soup)
        category = self._extract_category(soup)

        attributes = self._extract_attributes(soup)
        suppliers = self._extract_supplier_info(soup, url)

        return Product(
            title=title,
            description = description,
            article=article,
            brand=brand,
            country_of_origin=country_of_origin,
            warranty_months=warranty_months,
            category=category,
            attributes=attributes,
            suppliers=suppliers
        )

    def _extract_title(self, soup: BeautifulSoup) -> str:
        """Извлекает название товара"""

        h1_tag = soup.find('h1', class_ = 'ty-product-block-title')
        if h1_tag:
            return h1_tag.get_text(strip=True)

        return "Нет данных"

    def _extract_description(self, soup: BeautifulSoup) -> str:
        desc_prop = soup.find('div', class_='characteristicBox')
        if desc_prop:
            desc_tbody = desc_prop.find('tbody')
            if desc_tbody:
                rows = desc_tbody.find_all('tr')
                for row in rows:
                    cells = row.find_all('td')
                    if len(cells) >= 2:
                        name = cells[0].get_text(strip=True)
                        value = cells[1].get_text(strip=True)
                        if name.lower() == 'описание' and value and value != '-':
                            return value

        return "Нет данных"

    def _extract_article(self, soup: BeautifulSoup) -> str:
        """Извлекает артикул товара"""

        # Ищем артикул в основном блоке
        article_block = soup.find('div', class_ = 'ty-product-block__sku')
        if article_block:
            article_span = article_block.find('span', class_ = 'ty-control-group__item')
            if article_span:
                article_text = article_span.get_text(strip=True)
                if article_text and article_text.strip():
                    return article_text

        return "Нет данных"

    def _extract_brand(self, soup: BeautifulSoup) -> str:
        """Извлекает бренд товара"""

        # Ищем в основном блоке
        brand_block = soup.find('div', class_ = 'ty-features-list')
        if brand_block:
            brand_text = brand_block.get_text(strip=True)
            if brand_text and brand_text.strip():
                return brand_text

        # Ищем в блоке характеристик

        brand_prop = soup.find('div', class_='characteristicBox')
        if brand_prop:
            brand_tbody = brand_prop.find('tbody')
            if brand_tbody:
                rows = brand_tbody.find_all('tr')
                for row in rows:
                    cells = row.find_all('td')
                    if len(cells) >= 2:
                        name = cells[0].get_text(strip=True)
                        value = cells[1].get_text(strip=True)
                        if name == 'Производитель' and value and value != '-':
                            return value

        return "Нет данных"

    def _extract_stock(self, soup: BeautifulSoup) -> str:
        """Извлекает наличие товара"""

        # Ищем в основном блоке товара
        stock_block = soup.find('div', class_ = 'ty-control-group product-list-field')
        if stock_block:
            span_stock = stock_block.find('span', class_ = 'ty-qty-in-stock ty-control-group__item')
            if span_stock:
                stock_text = span_stock.get_text(strip=True)
                if stock_text and stock_text.strip():
                    return stock_text

        return "Нет данных"

    def _extract_country(self, soup: BeautifulSoup) -> str:
        """Извлекает страну производителя"""

        # Список возможных названий поля для страны
        country_field_names = [
            'Страна изготовления товара',
            'manufacturerCountry',
            'Страна производителя',
            'Страна-производитель',
            'Страна изготовитель',
            'Country',
            'Manufacturer Country',
            'Country of Origin'
        ]

        # Ищем в блоке характеристик
        properties_block = soup.find('div', class_='characteristicBox')
        if properties_block:
            country_tbody = properties_block.find('tbody')
            if country_tbody:
                rows = country_tbody.find_all('tr')
                for row in rows:
                    cells = row.find_all('td')
                    if len(cells) >= 2:
                        name = cells[0].get_text(strip=True)
                        value = cells[1].get_text(strip=True)
                        if name in country_field_names and value and value != '-':
                            return value

                        name_lower = name.lower()
                        for field_name in country_field_names:
                            if field_name.lower() in name_lower and value and value != '-':
                                return value

        return "Нет данных"

    def _extract_price(self, soup: BeautifulSoup) -> float:
        """Извлекает цену товара"""

        price_block = soup.find('span', class_ = 'ty-price')
        if price_block:
            price_str = price_block.find('span', class_ = 'ty-price-num')
            if price_str:
                price_text = price_str.get_text(strip=True)
                if price_text and price_text.strip():
                    price = re.sub(r'[^\d,.]', '', price_text)
                    price = price.replace(',', '.')
                    try:
                        return float(price)
                    except ValueError:
                        logger.warning(f"Не удалось конвертировать цену в число: {price_text}")
                        return 0.0

        return 0.0

    def _extract_warranty_months(self, soup: BeautifulSoup) -> str:
        """Извлекает гарантию товара"""

        # Ищем в блоке характеристик
        properties_block = soup.find('div', class_='characteristicBox')
        if properties_block:
            warranty_tbody = properties_block.find('tbody')
            if warranty_tbody:
                rows = warranty_tbody.find_all('tr')
                for row in rows:
                    cells = row.find_all('td')
                    if len(cells) >= 2:
                        name = cells[0].get_text(strip=True)
                        value = cells[1].get_text(strip=True)
                        if name == 'Гарантия' and value and value != '-':
                            return value

        return "Нет данных"

    def _extract_category(self, soup: BeautifulSoup) -> str:
        """Извлекает категорию товара"""

        category_block = soup.find('div', class_ = 'ty-breadcrumbs clearfix')
        if category_block:
            category_items = category_block.find_all('a')

            categories = []
            for item in category_items:
                category = item.get_text(strip=True)
                if category:
                    categories.append(category)

            if categories:
                return categories[-1]

        return "Нет данных"

    def _extract_attributes(self, soup: BeautifulSoup) -> List[Attribute]:
        """Извлекает атрибуты товара, избегая дублирования"""

        attributes = []
        seen_attributes = set()

        excluded_attributes = {
            'название', 'бренд', 'производитель', 'артикул', 'цена', 'стоимость', 'наличие',
            'в наличии', 'гарантия', 'страна изготовления товара', 'категория', 'описание',
            'manufacturerCountry'
        }

        attr_block = soup.find('div', class_='characteristicBox')
        if attr_block:
            tbody = attr_block.find('tbody')
            if tbody:
                rows = tbody.find_all('tr')
                for row in rows:
                    cells = row.find_all('td')
                    if len(cells) >= 2:
                        name = cells[0].get_text(strip=True)
                        value = cells[1].get_text(strip=True)

                        name_lower = name.lower()

                        if (name_lower in excluded_attributes or
                                not value or
                                value.strip() == '-' or
                                value.strip() == '' or
                                name in seen_attributes):
                            continue

                        # Пропускаем заголовки секций
                        if not value.strip() or cells[0].find('b') or name.endswith('характеристики'):
                            continue

                        attributes.append(Attribute(attr_name = name, attr_value = value))
                        seen_attributes.add(name_lower)

                        logger.debug(f"Добавлен атрибут: {name} = {value}")

        logger.info(f"Извлечено атрибутов: {len(attributes)}")
        return attributes

    def _extract_supplier_info(self, soup: BeautifulSoup, page_url: str) -> List[Supplier]:
        """Извлекает информацию о поставщике"""

        price = self._extract_price(soup)
        stock = self._extract_stock(soup)

        price_info = PriceInfo(qnt = 1, discount = 0, price = price)

        supplier_offer = SupplierOffer(
            price = [price_info],
            stock = stock,
            purchase_url = page_url
        )

        supplier = Supplier(
            supplier_name = 'Alecomp',
            supplier_tel = '+7 495 984-51-56',
            supplier_address = 'г. Москва, ул. 2-ая Фрезерная, 14 стр.1Б',
            supplier_description = 'Компьютерный центр Алекомп занимается продажей компьютеров и оргтехники с 2006 года. Нашими покупателями стали сотни компаний из различных секторов экономики. Корпоративные клиенты предъявляют особые требования к надежности поставщиков, поэтому поставщик компьютерной техники Алекомп уделяет особое внимание удобству работы и надежности поставок. В нашем компьютерном магазине собраны все актуальные товары для надежной работы офиса. Мы гарантируем быструю доставку купленного у нас компьютерного оборудования!',
            supplier_offers = [supplier_offer]
        )

        return [supplier]



