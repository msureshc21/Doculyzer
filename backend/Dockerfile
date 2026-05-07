FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

RUN pip install --no-cache-dir --upgrade pip

# Install base requirements by default (keeps docker builds fast).
# ML deps are optional and can be installed via:
#   docker compose build --build-arg INSTALL_ML=1 backend
ARG INSTALL_ML=0
COPY requirements-base.txt /app/requirements-base.txt
COPY requirements-ml.txt /app/requirements-ml.txt
RUN pip install --no-cache-dir -r /app/requirements-base.txt && \
    if [ "$INSTALL_ML" = "1" ]; then pip install --no-cache-dir -r /app/requirements-ml.txt; fi

COPY . /app

# Store sqlite DB and uploads on a volume by default.
ENV DATABASE_URL="sqlite:////data/paperwork_copilot.db" \
    UPLOAD_DIR="/data/uploads"

EXPOSE 8000

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]

