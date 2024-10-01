# Use Ubuntu 22.04 as the base image
FROM ubuntu:22.04

# Avoid prompts from apt
ENV DEBIAN_FRONTEND=noninteractive

# Set the working directory in the container
WORKDIR /app

# Install system dependencies, Python, and pip
RUN apt-get update && apt-get install -y \
    python3 \
    python3-pip \
    wget \
    && rm -rf /var/lib/apt/lists/*

# Install SUMO 1.20.0
RUN wget https://sumo.dlr.de/releases/1.20.0/sumo_1.20.0-1_amd64.deb && \
    apt-get update && \
    apt-get install -y ./sumo_1.20.0-1_amd64.deb && \
    rm sumo_1.20.0-1_amd64.deb && \
    rm -rf /var/lib/apt/lists/*

# Set SUMO_HOME environment variable
ENV SUMO_HOME /usr/share/sumo

# Copy the current directory contents into the container at /app
COPY . /app

# Upgrade pip and install requirements
RUN python3 -m pip install --no-cache-dir --upgrade pip && \
    python3 -m pip install --no-cache-dir -r requirements.txt

# Make port 5000 available to the world outside this container
EXPOSE 5000

# Define environment variable
ENV FLASK_APP=app.py

# Run app.py when the container launches
CMD ["python3", "-m", "flask", "run", "--host=0.0.0.0"]
