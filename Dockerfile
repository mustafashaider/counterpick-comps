# downloads a lighter version of python
FROM python:3.11-slim

WORKDIR /app

# Copies the libraries in requirements.txt and installs them
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# copies main.py and seed.py into the container and opens port 8000 for FastAPI
COPY . .
EXPOSE 8000
# starts the server
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]