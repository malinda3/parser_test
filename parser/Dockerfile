FROM python:3.12-slim
WORKDIR /app
COPY requirements.txt .
COPY ProductParser.py .
COPY parser_handler.py .
RUN pip install --no-cache-dir -r requirements.txt
CMD ["python3", "parser_handler.py"]