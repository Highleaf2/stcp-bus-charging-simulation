import os
from dotenv import load_dotenv

load_dotenv()

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
    "latitude": 41.152661,
    "longitude": -8.579658
}

TELEMETRY_INTERVAL = 5