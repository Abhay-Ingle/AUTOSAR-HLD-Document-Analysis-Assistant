FROM python:3.11-slim
WORKDIR /app
COPY pyproject.toml README.md ./
COPY app ./app
COPY ui ./ui
RUN pip install --no-cache-dir .
EXPOSE 8501
CMD ["uvicorn", "ui.web:app", "--host", "0.0.0.0", "--port", "8501"]
