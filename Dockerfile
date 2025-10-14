# Use a lightweight Python image
FROM python:3.10-slim

# Set working directory
WORKDIR /app

# Copy only requirements first for better caching
COPY requirements.txt .

# Upgrade pip and install dependencies
RUN pip install --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Copy application code and data
COPY . .

# Expose the port the app runs on (must match PORT env var)
ENV PORT=8080
EXPOSE 8080

# Start the bot
CMD ["python", "bot.py"]
