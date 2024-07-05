# Use an official Python runtime as a parent image
FROM python:3.10-slim

# Set the working directory
WORKDIR /app

# Copy the current directory contents into the container at /app
COPY . /app

# Install any needed packages specified in requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Install spaCy and the English model
RUN pip install spacy && python -m spacy download en_core_web_sm

# Make port 5000 available to the world outside this container
EXPOSE 5000

# Run the application
CMD ["python", "app/routes.py"]
