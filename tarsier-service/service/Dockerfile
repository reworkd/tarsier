# Use the official Python 3.12 image as the base
FROM python:3.12-slim

# Set environment variables
ENV POETRY_VERSION=1.8.3

# Install Poetry
RUN pip install --no-cache-dir "poetry==$POETRY_VERSION"

# Set the working directory in the container
WORKDIR /app
USER root

COPY poetry.lock pyproject.toml .

# Install dependencies defined in poetry.lock
RUN poetry config virtualenvs.create false && poetry install

COPY . .

# Command to run the application
# CMD ["poetry", "run", "python", "src/main.py"]
CMD ["python", "src/main.py"]
