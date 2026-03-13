import os
from dotenv import load_dotenv

# Azure Device Provisioning Service (DPS)
PROVISIONING_HOST = "global.azure-devices-provisioning.net"
ID_SCOPE = "0ne011270BD"

load_dotenv()

# Azure IoT Central Configuration
ID_SCOPE = os.getenv("ID_SCOPE", "your-id-scope-here")

CHARGING_STATIONS = {
    "CS-001": {
        "device_id": "CS-001",
        "primary_key": os.getenv("CS_001_KEY", "your-key-here")
    },
    "CS-002": {
        "device_id": "CS-002",
        "primary_key": os.getenv("CS_002_KEY", "your-key-here")
    },
    "CS-003": {
        "device_id": "CS-003",
        "primary_key": os.getenv("CS_003_KEY", "your-key-here")
    }
}

ELECTRIC_BUSES = {
    "BUS-001": {
        "device_id": "BUS-001",
        "primary_key": os.getenv("BUS_001_KEY", "your-key-here"),
        "route": "Route-700",
        "departure_time": "08:30"
    },
    "BUS-002": {
        "device_id": "BUS-002",
        "primary_key": os.getenv("BUS_002_KEY", "your-key-here"),
        "route": "Route-800",
        "departure_time": "09:00"
    },
    "BUS-003": {
        "device_id": "BUS-003",
        "primary_key": os.getenv("BUS_003_KEY", "your-key-here"),
        "route": "Route-900",
        "departure_time": "07:45"
    }
}

STATION_LOCATION = {
    "latitude": 41.1781,
    "longitude": -8.6081
}

TELEMETRY_INTERVAL = 1

# Chaves específicas dos dispositivos
BUS_001_KEY = "vOGfWe1WJqRbFajnsw5PP3x/KsS0UvBY9E+DyvaLKoQ="
BUS_002_KEY = "DCzNgN6u5GjJ1sJCit1bSfsqYKZdYctHkdW+e2Hb6rg="
BUS_003_KEY = "y2wdMxN7Awcg21DeKhEuViw7W9zBHGjCsh3BvOq02zo="
CS_001_KEY = "PhcPUbFBCAk/4ljat0fTfe6y7PZpyiO2DLrI+hVs+jI="
CS_002_KEY = "LggcAWtMwCjXkyyWpEabLvlq4S+95lo8icIV+0Ids7E="
CS_003_KEY = "bQyQqPbnMl2PGOhg+ZcsQJecnMfjTcBY5VqQOGzZy5I="

def get_device_key(device_id):
    """Obter chave específica do dispositivo"""
    device_keys = {
        "BUS-001": BUS_001_KEY,
        "BUS-002": BUS_002_KEY,
        "BUS-003": BUS_003_KEY,
        "CS-001": CS_001_KEY,
        "CS-002": CS_002_KEY,
        "CS-003": CS_003_KEY
    }
    return device_keys.get(device_id)