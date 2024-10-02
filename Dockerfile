# Stage 1: Build SUMO from source
FROM python:3.8-bullseye AS builder

LABEL maintainer="Your Name (your.email@example.com)"
LABEL description="Dockerised Simulation of Urban MObility (SUMO)"

ENV SUMO_VERSION 1_20_0
ENV SUMO_HOME /opt/sumo

# Install build dependencies
RUN apt-get update && apt-get -qq install -y \
    build-essential \
    cmake \
    libxerces-c-dev \
    libfox-1.6-dev \
    libgdal-dev \
    libproj-dev \
    swig \
    python3 \
    git \
    && rm -rf /var/lib/apt/lists/*

# Download and extract SUMO source code
RUN cd /tmp && \
    wget -q -O sumo.tar.gz https://github.com/eclipse/sumo/archive/v${SUMO_VERSION}.tar.gz && \
    tar xzf sumo.tar.gz && \
    mv sumo-${SUMO_VERSION} $SUMO_HOME && \
    rm sumo.tar.gz

# Configure and build SUMO from source
RUN cd $SUMO_HOME && \
    mkdir build && \
    cd build && \
    cmake .. && \
    make -j$(nproc)

# Stage 2: Create final image
FROM python:3.8-bullseye

LABEL maintainer="Your Name (your.email@example.com)"
LABEL description="Dockerised Simulation of Urban MObility (SUMO)"

ENV SUMO_VERSION 1_20_0
ENV SUMO_HOME /opt/sumo
ENV PYTHONPATH="${SUMO_HOME}/tools"
ENV PATH="${SUMO_HOME}/bin:${PATH}"

# Install runtime dependencies
RUN apt-get update && apt-get -qq install -y \
    libgdal28 \
    libfox-1.6-0 \
    libgl1 \
    libgl2ps1.4 \
    libglu1-mesa \
    libproj19 \
    libxerces-c3.2 \
    && rm -rf /var/lib/apt/lists/*

# Copy SUMO from the builder stage
COPY --from=builder $SUMO_HOME $SUMO_HOME

# Set working directory
WORKDIR /app

# Copy application code into /app
COPY . /app

# Upgrade pip and install Python dependencies
RUN pip install --no-cache-dir --upgrade pip setuptools wheel

# Remove 'traci' and 'sumolib' from requirements.txt if present
RUN grep -vE "^(traci|sumolib)" requirements.txt > temp_requirements.txt && \
    pip install --no-cache-dir -r temp_requirements.txt && \
    rm temp_requirements.txt

# Expose port 5000
EXPOSE 5000

# Run your Flask app
CMD ["python", "app.py"]
