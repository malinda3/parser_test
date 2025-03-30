FROM python:3.12-slim
WORKDIR /app
COPY requirements.txt .
COPY ProductParser.py .
COPY parser_handler.py .
RUN pip install --no-cache-dir -r requirements.txt
CMD ["uvicorn", "parser_handler:app", "--host", "0.0.0.0", "--port", "8000"]