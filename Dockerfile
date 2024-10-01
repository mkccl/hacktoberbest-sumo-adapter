# Use an official Python runtime as a parent image
FROM python:3.9-slim

# Set the working directory in the container
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    wget \
    gnupg2 \
    software-properties-common \
    && rm -rf /var/lib/apt/lists/*

# Add SUMO repository
RUN wget -O - https://dist.eclipse.org/sumo/1.18.0/sumo-1.18.0-key.pub | apt-key add - \
    && add-apt-repository "deb https://dist.eclipse.org/sumo/1.18.0/bin/linux/debian bullseye main"

# Install SUMO
RUN apt-get update && apt-get install -y \
    sumo sumo-tools sumo-doc \
    && rm -rf /var/lib/apt/lists/*

# Set SUMO_HOME environment variable
ENV SUMO_HOME /usr/share/sumo

# Copy the current directory contents into the container at /app
COPY . /app

# Install any needed packages specified in requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Make port 5000 available to the world outside this container
EXPOSE 5000

# Define environment variable
ENV FLASK_APP=app.py

# Run app.py when the container launches
CMD ["flask", "run", "--host=0.0.0.0"]
