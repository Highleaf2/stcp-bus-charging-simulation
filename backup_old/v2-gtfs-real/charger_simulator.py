"""
STCP Charging Station Simulator - Realistic Version
Implements realistic charging behavior with power modulation
"""

import random
import time

class ChargerState:
    """Charger operational states"""
    IDLE = "IDLE"                    # No bus connected
    CHARGING = "CHARGING"            # Actively charging a bus
    FAULT = "FAULT"                  # Error state
    MAINTENANCE = "MAINTENANCE"      # Maintenance mode

class ChargerSimulator:
    """
    Simulates realistic charging station behavior with:
    - Variable power output (0-150 kW)
    - Temperature increase during charging
    - Efficiency losses
    - Energy metering
    """
    
    def __init__(self, device_id):
        self.device_id = device_id
        
        # Charger specifications
        self.MAX_POWER_KW = 150.0              # Maximum output power
        self.EFFICIENCY = random.uniform(0.90, 0.95)  # 90-95% efficiency
        
        # Current state
        self.state = ChargerState.IDLE
        self.current_power_kw = 0.0            # Current output power
        self.charger_temperature = random.uniform(18, 22)  # °C
        
        # Energy tracking
        self.total_energy_delivered_kwh = 0.0  # Total energy delivered (session)
        self.session_start_time = None
        self.session_energy_kwh = 0.0
        
        # Connected bus
        self.connected_bus = None
        
        # Telemetry timing
        self.last_update_time = time.time()
        
        print(f"[{self.device_id}] Initialized - Efficiency: {self.EFFICIENCY*100:.1f}%")
    
    def connect_bus(self, bus_id):
        """Connect a bus to this charger"""
        if self.state == ChargerState.IDLE:
            self.connected_bus = bus_id
            self.state = ChargerState.CHARGING
            self.session_start_time = time.time()
            self.session_energy_kwh = 0.0
            print(f"[{self.device_id}] Bus {bus_id} connected")
            return True
        return False
    
    def disconnect_bus(self):
        """Disconnect bus from charger"""
        if self.connected_bus:
            session_duration = time.time() - self.session_start_time
            print(f"[{self.device_id}] Bus {self.connected_bus} disconnected - "
                  f"Session: {session_duration/60:.1f}min, "
                  f"Energy: {self.session_energy_kwh:.2f} kWh")
            
        self.connected_bus = None
        self.state = ChargerState.IDLE
        self.current_power_kw = 0.0
        self.session_start_time = None
        self.session_energy_kwh = 0.0
    
    def set_charging_power(self, requested_power_kw, bus_battery_percent):
        """
        Set charging power based on battery level
        Implements realistic charging curve (reduces power when battery is full)
        """
        if self.state != ChargerState.CHARGING:
            self.current_power_kw = 0.0
            return 0.0
        
        # Reduce power as battery fills (realistic charging curve)
        if bus_battery_percent < 20:
            power_multiplier = 0.7  # Slower charging when very low (battery protection)
        elif bus_battery_percent < 80:
            power_multiplier = 1.0  # Full power in middle range
        elif bus_battery_percent < 90:
            power_multiplier = 0.7  # Reduce power above 80%
        else:
            power_multiplier = 0.3  # Trickle charge above 90%
        
        # Apply maximum power limit
        target_power = min(requested_power_kw * power_multiplier, self.MAX_POWER_KW)
        
        # Smooth power changes (simulate power ramping)
        if abs(target_power - self.current_power_kw) > 5:
            # Ramp up/down by 5 kW per update
            if target_power > self.current_power_kw:
                self.current_power_kw = min(target_power, self.current_power_kw + 5)
            else:
                self.current_power_kw = max(target_power, self.current_power_kw - 5)
        else:
            self.current_power_kw = target_power
        
        # Add small random variation (power fluctuation)
        self.current_power_kw += random.uniform(-0.5, 0.5)
        self.current_power_kw = max(0, min(self.MAX_POWER_KW, self.current_power_kw))
        
        return self.current_power_kw
    
    def _update_temperature(self, delta_time):
        """Update charger temperature based on load"""
        ambient_temp = 20.0
        
        if self.state == ChargerState.CHARGING and self.current_power_kw > 0:
            # Heat generation proportional to power and losses
            power_ratio = self.current_power_kw / self.MAX_POWER_KW
            heat_generation = (1 - self.EFFICIENCY) * 100  # Convert efficiency loss to heat
            
            # Target temperature increases with load
            target_temp = ambient_temp + (heat_generation * power_ratio)
        else:
            # Cool down to ambient
            target_temp = ambient_temp
        
        # Gradual temperature change
        temp_change_rate = 0.2 * delta_time  # Degrees per second
        if self.charger_temperature < target_temp:
            self.charger_temperature = min(target_temp, self.charger_temperature + temp_change_rate)
        else:
            self.charger_temperature = max(target_temp, self.charger_temperature - temp_change_rate)
        
        # Add small random variation
        self.charger_temperature += random.uniform(-0.1, 0.1)
        self.charger_temperature = max(15, min(45, self.charger_temperature))
    
    def update(self):
        """Update charger state - call this regularly"""
        current_time = time.time()
        delta_time = current_time - self.last_update_time
        
        # Update temperature
        self._update_temperature(delta_time)
        
        # Track energy delivered
        if self.state == ChargerState.CHARGING and self.current_power_kw > 0:
            hours = delta_time / 3600.0
            energy_delivered = self.current_power_kw * hours
            self.session_energy_kwh += energy_delivered
            self.total_energy_delivered_kwh += energy_delivered
        
        self.last_update_time = current_time
    
    def get_telemetry(self):
        """Get current telemetry data"""
        return {
            "chargerTemperature": round(self.charger_temperature, 2),
            "currentEfficiency": round(self.EFFICIENCY * 100, 2),
            "currentPower": round(self.current_power_kw, 2),
            "energyDelivered": round(self.session_energy_kwh, 2),
            "state": self.state,
            "connectedBus": self.connected_bus,
            "totalEnergyDelivered": round(self.total_energy_delivered_kwh, 2)
        }
