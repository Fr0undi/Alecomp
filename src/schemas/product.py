from typing import List
from pydantic import BaseModel, Field
from datetime import datetime


class PriceInfo(BaseModel):
    qnt: int = 1
    discount: float
    price: float


class SupplierOffer(BaseModel):
    price: List[PriceInfo]
    stock: str = 'Нет данных'
    delivery_time: str = 'Доставка 1-2 дня'
    package_info: str = 'Нет данных'
    purchase_url: str


class Supplier(BaseModel):
    dealer_id: str = 'Нет данных'
    supplier_name: str = 'Alecomp'
    supplier_tel: str = '+7 495 984-51-56'
    supplier_address: str = 'г. Москва, ул. 2-ая Фрезерная, 14 стр.1Б'
    supplier_description: str = 'Компьютерный центр Алекомп занимается продажей компьютеров и оргтехники с 2006 года. Нашими покупателями стали сотни компаний из различных секторов экономики. Корпоративные клиенты предъявляют особые требования к надежности поставщиков, поэтому поставщик компьютерной техники Алекомп уделяет особое внимание удобству работы и надежности поставок. В нашем компьютерном магазине собраны все актуальные товары для надежной работы офиса. Мы гарантируем быструю доставку купленного у нас компьютерного оборудования!'
    supplier_offers: List[SupplierOffer] = Field(default_factory=list)


class Attribute(BaseModel):
    attr_name: str
    attr_value: str


class Product(BaseModel):
    title: str
    description: str = 'Нет данных'
    article: str
    brand: str
    country_of_origin: str = 'Нет данных'
    warranty_months: str = 'Нет данных'
    category: str = 'Нет данных'
    created_at: str = Field(
        default_factory=lambda: datetime.now().strftime("%d.%m.%Y %H:%M")
    )
    attributes: List[Attribute] = Field(default_factory=list)
    suppliers: List[Supplier] = Field(default_factory=list)