# Use Ubuntu 22.04 as the base image
FROM ubuntu:22.04

# Avoid prompts from apt
ENV DEBIAN_FRONTEND=noninteractive

# Set the working directory in the container
WORKDIR /app

# Install system dependencies and Python 3.12
RUN apt-get update && apt-get install -y \
    software-properties-common \
    && add-apt-repository ppa:deadsnakes/ppa \
    && apt-get update \
    && apt-get install -y \
    python3.12 \
    python3.12-venv \
    python3.12-dev \
    python3-pip \
    wget \
    && rm -rf /var/lib/apt/lists/*

# Install SUMO 1.20.0
RUN wget https://sumo.dlr.de/releases/1.20.0/sumo-src-1.20.0.tar.gz \
    && tar -xzf sumo-src-1.20.0.tar.gz \
    && cd sumo-1.20.0 \
    && apt-get update && apt-get install -y cmake libxerces-c-dev libfox-1.6-dev libgdal-dev libproj-dev libgl2ps-dev \
    && mkdir build/cmake-build && cd build/cmake-build \
    && cmake ../.. \
    && make -j$(nproc) \
    && make install \
    && cd /app \
    && rm -rf sumo-src-1.20.0.tar.gz sumo-1.20.0 \
    && rm -rf /var/lib/apt/lists/*

# Set SUMO_HOME environment variable
ENV SUMO_HOME /usr/local/share/sumo

# Copy the current directory contents into the container at /app
COPY . /app

# Upgrade pip and install requirements
RUN python3.12 -m pip install --no-cache-dir --upgrade pip && \
    python3.12 -m pip install --no-cache-dir -r requirements.txt

# Make port 5000 available to the world outside this container
EXPOSE 5000

# Define environment variable
ENV FLASK_APP=app.py

# Run app.py when the container launches
CMD ["python3.12", "-m", "flask", "run", "--host=0.0.0.0"]
