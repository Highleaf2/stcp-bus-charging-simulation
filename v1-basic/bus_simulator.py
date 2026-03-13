"""
STCP Electric Bus Simulator - Realistic Version
Implements state machine with realistic battery behavior
"""

import random
import time
import math
from datetime import datetime
from enum import Enum

class BusState(Enum):
    """Bus operational states"""
    PARKED = "PARKED"                    # In depot, systems off
    IDLE_DEPOT = "IDLE_DEPOT"           # In depot, systems on
    CHARGING = "CHARGING"                # Actively charging
    ROUTE = "ROUTE"                      # Driving on route
    IDLE_ON_ROUTE = "IDLE_ON_ROUTE"     # Stopped at bus stop/traffic light

class BusSimulator:
    """
    Simulates realistic electric bus behavior with:
    - Battery discharge during operation
    - Self-discharge when parked
    - Charging from stations
    - State transitions
    - Temperature management
    """
    
    def __init__(self, device_id, initial_battery_percent=None):
        self.device_id = device_id
        
        # Battery specifications
        self.BATTERY_CAPACITY_KWH = 350.0  # Total battery capacity
        
        # Initialize battery level (different for each bus)
        if initial_battery_percent is None:
            # Randomize initial state for realism
            self.battery_percent = random.uniform(50, 70)
        else:
            self.battery_percent = initial_battery_percent
        
        self.battery_kwh = (self.battery_percent / 100.0) * self.BATTERY_CAPACITY_KWH
        self.battery_temperature = random.uniform(18, 22)  # °C
        
        # Consumption rates (kW)
        self.CONSUMPTION_PARKED = 0.0           # No consumption when fully off
        self.CONSUMPTION_IDLE = random.uniform(2, 3)  # HVAC, computers, lights
        self.CONSUMPTION_ROUTE_BASE = 80        # Base consumption while driving (kW)
        self.CONSUMPTION_PER_KM = 1.5           # kWh per km average
        
        # Self-discharge rate
        self.SELF_DISCHARGE_RATE = 0.3 / 3600   # 0.3% per hour = 0.3/3600 per second
        
        # Charging parameters
        self.MAX_CHARGING_POWER_KW = 150        # Maximum charging power
        self.current_charging_power = 0          # Current charging power (kW)
        self.connected_charger_id = None         # Which charger we're connected to
        
        # Movement and location
        self.latitude = 41.1781   # Porto coordinates
        self.longitude = -8.6081
        self.speed_kmh = 0
        
        # State management
        self.state = BusState.PARKED
        self.state_start_time = time.time()
        self.time_in_state = 0
        
        # Telemetry timing
        self.last_telemetry_time = time.time()
        
        print(f"[{self.device_id}] Initialized - Battery: {self.battery_percent:.1f}% ({self.battery_kwh:.1f} kWh), State: {self.state.value}")
    
    def _calculate_remaining_range_km(self):
        """Calculate remaining range based on current battery"""
        # Average consumption: 1.5 kWh/km
        return self.battery_kwh / self.CONSUMPTION_PER_KM
    
    def _update_battery_temperature(self, delta_time):
        """Update battery temperature based on activity"""
        ambient_temp = 20.0
        
        if self.state == BusState.CHARGING:
            # Heating during charging (up to 35°C)
            target_temp = 30 + (self.current_charging_power / self.MAX_CHARGING_POWER_KW) * 5
        elif self.state == BusState.ROUTE:
            # Heating during driving (up to 30°C)
            target_temp = 25 + (self.speed_kmh / 50) * 5
        elif self.state == BusState.IDLE_ON_ROUTE:
            # Slight heating from systems
            target_temp = 23
        else:
            # Cooling toward ambient
            target_temp = ambient_temp
        
        # Gradual temperature change
        temp_change_rate = 0.1 * delta_time  # Degrees per second
        if self.battery_temperature < target_temp:
            self.battery_temperature = min(target_temp, self.battery_temperature + temp_change_rate)
        else:
            self.battery_temperature = max(target_temp, self.battery_temperature - temp_change_rate)
        
        # Add small random variation
        self.battery_temperature += random.uniform(-0.1, 0.1)
        self.battery_temperature = max(15, min(40, self.battery_temperature))
    
    def _apply_self_discharge(self, delta_time):
        """Apply self-discharge to battery"""
        if self.state == BusState.PARKED:
            # Self-discharge when fully powered off
            discharge_percent = self.SELF_DISCHARGE_RATE * delta_time
            self.battery_percent -= discharge_percent
    
    def _apply_idle_consumption(self, delta_time):
        """Apply consumption when systems are on but not moving"""
        if self.state in [BusState.IDLE_DEPOT, BusState.IDLE_ON_ROUTE]:
            # Convert time to hours
            hours = delta_time / 3600.0
            kwh_consumed = self.CONSUMPTION_IDLE * hours
            
            self.battery_kwh -= kwh_consumed
            self.battery_percent = (self.battery_kwh / self.BATTERY_CAPACITY_KWH) * 100
    
    def _apply_driving_consumption(self, delta_time):
        """Apply consumption while driving"""
        if self.state == BusState.ROUTE and self.speed_kmh > 0:
            # Distance traveled in this time step
            hours = delta_time / 3600.0
            km_traveled = self.speed_kmh * hours
            
            # Energy consumed
            kwh_consumed = km_traveled * self.CONSUMPTION_PER_KM
            
            self.battery_kwh -= kwh_consumed
            self.battery_percent = (self.battery_kwh / self.BATTERY_CAPACITY_KWH) * 100
            
            # Update position (simplified - move along longitude)
            self.longitude += (km_traveled / 111.0) * random.choice([-1, 1]) * 0.01
    
    def start_charging(self, charger_id, charging_power_kw):
        """Connect to charger and start charging"""
        self.connected_charger_id = charger_id
        self.current_charging_power = min(charging_power_kw, self.MAX_CHARGING_POWER_KW)
        self.state = BusState.CHARGING
        self.state_start_time = time.time()
        print(f"[{self.device_id}] Started charging at {charger_id} - {self.current_charging_power:.1f} kW")
    
    def stop_charging(self):
        """Disconnect from charger"""
        if self.connected_charger_id:
            print(f"[{self.device_id}] Stopped charging - Battery: {self.battery_percent:.1f}%")
        self.connected_charger_id = None
        self.current_charging_power = 0
        self.state = BusState.IDLE_DEPOT
        self.state_start_time = time.time()
    
    def start_route(self):
        """Start driving route"""
        self.state = BusState.ROUTE
        self.state_start_time = time.time()
        self.speed_kmh = random.uniform(20, 40)  # City driving speed
        print(f"[{self.device_id}] Started route - Battery: {self.battery_percent:.1f}%")
    
    def stop_at_station(self):
        """Stop at bus station/traffic light"""
        self.state = BusState.IDLE_ON_ROUTE
        self.state_start_time = time.time()
        self.speed_kmh = 0
    
    def return_to_depot(self):
        """Return to depot"""
        self.state = BusState.IDLE_DEPOT
        self.state_start_time = time.time()
        self.speed_kmh = 0
        self.latitude = 41.1781   # Reset to depot
        self.longitude = -8.6081
        print(f"[{self.device_id}] Returned to depot - Battery: {self.battery_percent:.1f}%")
    
    def update(self):
        """Update bus state - call this regularly (e.g., every second)"""
        current_time = time.time()
        delta_time = current_time - self.last_telemetry_time
        self.time_in_state = current_time - self.state_start_time
        
        # Update battery based on state
        self._apply_self_discharge(delta_time)
        self._apply_idle_consumption(delta_time)
        self._apply_driving_consumption(delta_time)
        
        # Apply charging if connected
        if self.state == BusState.CHARGING and self.current_charging_power > 0:
            hours = delta_time / 3600.0
            # Charging efficiency: 92%
            kwh_added = self.current_charging_power * hours * 0.92
            self.battery_kwh = min(self.BATTERY_CAPACITY_KWH, self.battery_kwh + kwh_added)
            self.battery_percent = (self.battery_kwh / self.BATTERY_CAPACITY_KWH) * 100
            
            # Stop charging if full
            if self.battery_percent >= 95:
                self.stop_charging()
        
        # Update temperature
        self._update_battery_temperature(delta_time)
        
        # Ensure battery doesn't go negative
        self.battery_kwh = max(0, self.battery_kwh)
        self.battery_percent = max(0, self.battery_percent)
        
        self.last_telemetry_time = current_time
    
    def get_telemetry(self):
        """Get current telemetry data - simplified version"""
        return {
            "batteryKwh": round(self.battery_kwh, 2),
            "batteryLevel": round(self.battery_percent, 2),
            "batteryTemperature": round(self.battery_temperature, 2),
            "latitude": round(self.latitude, 4),
            "longitude": round(self.longitude, 4),
            "state": self.state.value
        }
