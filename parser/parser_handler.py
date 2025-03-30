import json
import logging
from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import JSONResponse
from ProductParser import ProductParser
from pydantic import BaseModel
import uuid

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI()

class ParseRequest(BaseModel):
    url: str
    request_id: str
    user_id: str

class ParseResponse(BaseModel):
    request_id: str
    user_id: str
    product_info: dict

@app.post("/parse")
async def parse_product(request: ParseRequest):
    """Ожидает на вход ссылку на товар, к ней должен прилагаться ID в телеграмме, и ид запроса"""
    """{Пример запроса, с которым роут работает "url": "https://faworldentertainment.com/collections/fa-best-sellers/products/fa-converse-chuck-70","request_id": "1","user_id": "1337"}"""
    """На выходе получается json вида {"request_id":"1","user_id":"1337","product_info":{"name":"FA Converse Chuck 70","price":"$110"}}"""
    try:
        logger.info(f"Processing URL: {request.url}")

        parser = ProductParser(request.url)
        product_info = parser.get_product_info()

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