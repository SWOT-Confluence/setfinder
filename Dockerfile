# Stage 0 - Create from Python3.12 image
FROM python:3.12-slim-bookworm as stage0
# FROM python:3.12-slim-bookworm

# Stage 1 - Debian dependencies
FROM stage0 as stage1
RUN apt update \
        && DEBIAN_FRONTEND=noninteractive apt install -y curl zip python3-dev build-essential libhdf5-serial-dev netcdf-bin libnetcdf-dev

# Stage 2 - Input Python dependencies
FROM stage1 as stage2
COPY requirements.txt /app/requirements.txt
RUN /usr/local/bin/python -m venv /app/env \
        && /app/env/bin/pip install -r /app/requirements.txt

# Stage 5 - Copy and execute module
FROM stage2 as stage3
COPY run_setfinder.py /app/run_setfinder.py
COPY ./sets /app/sets/
LABEL version="1.0" \
        description="Containerized setfinder module."
ENTRYPOINT ["/app/env/bin/python3", "/app/run_setfinder.py"]