import logging
from pymongo import AsyncMongoClient
from src.core.settings import settings

logger = logging.getLogger(__name__)


class MongoClient:

    def __init__(self):
        self.client = None
        self.database = None

    async def connect(self):
        self.client = AsyncMongoClient(settings.mongo_url)
        # Проверяем подключение
        await self.client.admin.command('ping')
        self.database = self.client[settings.db_name]
        logger.info(f"MongoDB подключен: {settings.db_name}")

    async def disconnect(self):
        if self.client:
            await self.client.close()

    def get_collection(self, name: str):
        return self.database[name]


mongo_client = MongoClient()