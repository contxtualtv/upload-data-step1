FROM python:3.11-slim

# Set the working directory in the container
WORKDIR /

# Copy the requirements file into the container
COPY requirements.txt .

# Install the required dependencies
RUN apt install libpq-dev python3-dev \
    && pip install --no-cache-dir -r requirements.txt

# Copy the rest of the application code into the container
COPY . .

# Expose the port that the application will run on
EXPOSE 8080

# Set the entry point to Gunicorn with the application
CMD ["gunicorn", "-b", ":8080", "--timeout", "3600", "main:app"]