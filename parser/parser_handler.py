import json
import logging
from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import JSONResponse
from ProductParser import ProductParser
from pydantic import BaseModel
import uuid

# Настройка логирования (как в оригинале)
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI()

# Модель запроса (аналогично Kafka-сообщению)
class ParseRequest(BaseModel):
    url: str
    request_id: str | None = None  # если не передадут, сгенерируем автоматически
    user_id: str | None = None     # опционально

# Модель ответа (аналогично Kafka-ответу)
class ParseResponse(BaseModel):
    request_id: str
    user_id: str | None
    product_info: dict

@app.post("/parse")
async def parse_product(request: ParseRequest):
    """Эндпоинт, который делает то же самое, что и Kafka-хендлер"""
    try:
        logger.info(f"Processing URL: {request.url}")

        # Вызываем ProductParser (синхронный код, но можно обернуть в threadpool)
        parser = ProductParser(request.url)
        product_info = parser.get_product_info()  # предполагаем, что это синхронный метод

        # Формируем ответ (как в Kafka-версии)
        response_data = {
            "request_id": request.request_id or str(uuid.uuid4()),
            "user_id": request.user_id,
            "product_info": product_info
        }

        logger.info(f"Successfully parsed: {response_data}")
        return JSONResponse(content=response_data)

    except Exception as e:
        logger.error(f"Error processing request: {e}")
        raise HTTPException(status_code=500, detail=str(e))