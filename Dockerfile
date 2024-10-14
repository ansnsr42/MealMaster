
# Python 3.9 Image 
FROM python:3.9-slim

# workdir
WORKDIR /app

# cp .
COPY . /app

# Installiere requiremntes
RUN pip install --upgrade pip
RUN pip install -r requirements.txt

# Expose Port 5000 
EXPOSE 5000

# Start Flask
CMD flask db upgrade && flask run --host=0.0.0.0 
