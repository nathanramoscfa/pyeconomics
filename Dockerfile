# Use the official Python image from the Docker Hub
FROM python:3.11-slim

# Set the working directory in the container
WORKDIR /app

# Copy the requirements file into the container
COPY requirements.txt .

# Install the dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy the entire project into the container
COPY . .

# Copy the start script into the container
COPY start.sh .

# Make the start script executable
RUN chmod +x start.sh

# Set environment variables for consistent behavior
ENV PYTHONUNBUFFERED=1

# Expose port 8888 for Jupyter Lab
EXPOSE 8888

# Start Jupyter Lab using the start script
CMD ["./start.sh"]
