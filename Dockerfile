# Based on https://github.com/thedirtyfew/dash-redis-mwe

FROM python:3.11-slim-buster

# Install gunicorn
RUN apt-get update
RUN apt-get install -y gunicorn
RUN apt-get install -y python-gevent

# Create a working directory.
RUN mkdir wd
WORKDIR wd

# Install Python dependencies.
COPY requirements.txt .
RUN pip install --upgrade virtualenv; \
    pip install --upgrade pip pip-tools setuptools wheel; \
    pip3 install -r requirements.txt

# Copy the rest of the codebase into the image
COPY . ./

# Finally, run gunicorn.
CMD [ "gunicorn", "--workers=5", "--threads=1", "-b 0.0.0.0:8000", "index:app"]