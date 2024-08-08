FROM python:3.11-slim
RUN pip install --no-cache-dir pdm

WORKDIR /app

COPY pyproject.toml pdm.lock /app/

RUN pdm add psycopg2-binary
# ^ yeah, I'm aware how big of a hack it is
RUN pdm install --prod --no-editable --frozen-lockfile

COPY src src

EXPOSE 8000
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1
CMD ["pdm", "run", "uvicorn", "src.applover_t1.app:app", "--host", "0.0.0.0", "--port", "8000" ]
