# Use an official lightweight Python image
FROM python:3.11.4

# Set the working directory in the container
WORKDIR /app

# Install system dependencies (if any)
# RUN apt-get update && apt-get install -y --no-install-recommends [packages]

# Copy poetry.lock and pyproject.toml
COPY pyproject.toml poetry.lock ./

# Install Python dependencies
RUN pip install poetry && poetry config virtualenvs.create false && poetry install --only main

# Install Playwright and its dependencies
RUN playwright install chromium
RUN playwright install-deps chromium

# Copy the rest of the application's code
COPY . .

# Inform Docker that the container listens on the specified port at runtime.
EXPOSE 4000

RUN ls -la /app

# Define the command to run the Flask application
CMD ["bash", "run.sh"]
