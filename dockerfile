FROM python:3.12-slim
WORKDIR /app
COPY . /app
RUN cat -A requirements.txt && pip install -r requirements.txt

EXPOSE 8000

CMD ["gunicorn", "sistematica.wsgi:application", "--bind", "0.0.0.0:8000"]

