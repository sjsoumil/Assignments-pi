# Use the official Python image from the Docker Hub
FROM python:3.11-slim

# Set the working directory inside the container
WORKDIR /app

# Copy the requirements file (if you have one, e.g., poetry.lock or requirements.txt)
COPY pyproject.toml /app/
COPY poetry.lock /app/

# Install Poetry to manage dependencies
RUN pip install poetry

# Install dependencies
RUN poetry install --no-root --no-dev

# Copy the entire project into the container
COPY . /app/

# Expose the port that FastAPI will run on
EXPOSE 8000

# Set environment variables (if needed)
ENV OPENAI_API_KEY=your_openai_api_key

# Command to run the FastAPI application using Uvicorn
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]
