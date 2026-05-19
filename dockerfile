# Start from a Python base image
FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Copy requirements.txt
COPY requirements.txt .

# Copy Python dependencies directory
COPY django_deps /django_deps

# Install Python dependencies from offline directory
RUN pip install --no-index --find-links=/django_deps -r requirements.txt
Run pip list

# Copy the app code
COPY . .
RUN python manage.py collectstatic --noinput
# Run the app
COPY consul/orders.json /app/consul/orders.json
COPY entrypoint.sh /app/entrypoint.sh

RUN chmod +x /app/entrypoint.sh

CMD ["/app/entrypoint.sh"]
