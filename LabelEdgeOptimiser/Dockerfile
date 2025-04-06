FROM python:3.12.9

# Install system dependencies for PyQt5 and XCB
RUN apt-get update && apt-get install -y \
    libgl1-mesa-glx \
    libxcb-xinerama0 \
    && rm -rf /var/lib/apt/lists/*

# Uncomment this if you want to run in offscreen mode (no GUI display)
# ENV QT_QPA_PLATFORM=offscreen

WORKDIR /app

# Copy the requirements and install dependencies
COPY requirements.txt ./
RUN pip install -r requirements.txt

# Copy all the application files
COPY . .

EXPOSE 5000

CMD ["python", "OptimiseApp.py"]
