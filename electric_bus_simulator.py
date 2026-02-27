# electric_bus_simulator.py
# Simulates an electric bus that sends telemetry to Azure IoT Central

import asyncio
import json
import random
from datetime import datetime
from azure.iot.device.aio import IoTHubDeviceClient, ProvisioningDeviceClient
from azure.iot.device import Message

class ElectricBusSimulator:
    """
    Represents a single electric bus device.
    Manages connection to Azure IoT Central and simulates bus behavior.
    Simulates battery discharge during transit and charging when connected to a station.
    """
    
    def __init__(self, device_id, id_scope, primary_key, route, departure_time, station_location):
        """
        Initialize the electric bus with Azure credentials and initial state.
        
        Args:
            device_id: Unique identifier (e.g., "BUS-001")
            id_scope: Azure IoT Central application ID scope
            primary_key: Authentication key from Azure IoT Central
            route: Assigned route (e.g., "Route-700")
            departure_time: Scheduled departure (e.g., "08:30")
            station_location: Dict with latitude and longitude of base station
        """
        # Azure connection parameters
        self.device_id = device_id
        self.id_scope = id_scope
        self.primary_key = primary_key
        self.client = None  # Will hold the Azure IoT Hub client once connected
        
        # Bus properties (fixed characteristics that don't change)
        self.battery_capacity = 350.0  # Total battery capacity in kWh
        self.model = "CaetanoBus e.City Gold"  # Bus model
        self.assigned_route = route  # Assigned route name
        self.scheduled_departure = departure_time  # Scheduled departure time
        self.avg_consumption = 1.2  # Average consumption in kWh per km
        
        # Bus state (variable characteristics that change over time)
        self.operational_status = "parked"  # Can be: parked, charging, inTransit, inactive
        
        # Start with varied battery levels (40-75%) to make simulation realistic
        self.battery_level = random.uniform(40, 75)  # Battery level as percentage
        
        # Calculate actual kWh from percentage
        self.battery_kwh = (self.battery_level / 100) * self.battery_capacity
        
        # GPS location (starts at base station)
        self.latitude = station_location["latitude"]
        self.longitude = station_location["longitude"]
        
        # Other telemetry variables
        self.instant_consumption = 0.0  # Current power consumption in kW
        self.remaining_range = self.battery_kwh / self.avg_consumption  # Remaining range in km
        self.battery_temperature = random.uniform(18, 25)  # Battery temperature in Celsius
        
        # Charging state
        self.connected_charger = None  # ID of connected charger (None if not charging)
        self.charging_power = 0.0  # Power being received when charging (kW)
        
    async def provision_device(self):
        """
        Register this device with Azure IoT Central using DPS (Device Provisioning Service).
        Same process as charging stations - DPS assigns device to correct IoT Hub.
        
        Returns:
            String with the assigned IoT Hub hostname
            
        Raises:
            RuntimeError if registration fails
        """
        # Create provisioning client with credentials
        provisioning_client = ProvisioningDeviceClient.create_from_symmetric_key(
            provisioning_host="global.azure-devices-provisioning.net",
            registration_id=self.device_id,
            id_scope=self.id_scope,
            symmetric_key=self.primary_key
        )
        
        # Register device with Azure
        registration_result = await provisioning_client.register()
        
        # Check registration status
        if registration_result.status == "assigned":
            return registration_result.registration_state.assigned_hub
        else:
            raise RuntimeError(f"Registration failed: {registration_result.status}")
    
    async def connect(self):
        """
        Establish connection to Azure IoT Central.
        
        Steps:
        1. Provision device via DPS
        2. Build connection string
        3. Create IoT Hub client
        4. Connect to Azure
        5. Send initial properties
        """
        try:
            # Get assigned IoT Hub from DPS
            assigned_hub = await self.provision_device()
            
            # Build connection string
            conn_str = f"HostName={assigned_hub};DeviceId={self.device_id};SharedAccessKey={self.primary_key}"
            
            # Create client
            self.client = IoTHubDeviceClient.create_from_connection_string(conn_str)
            
            # Connect to Azure
            await self.client.connect()
            print(f"Connected: {self.device_id}")
            
            # Send initial properties
            await self.update_properties()
            
        except Exception as e:
            print(f"Error connecting {self.device_id}: {e}")
            raise
    
    async def update_properties(self):
        """
        Update device twin properties in Azure IoT Central.
        
        Properties for buses include both fixed characteristics (model, capacity)
        and current operational state (status, assigned route, departure time).
        
        Properties sent:
        - batteryCapacity: Total battery capacity (fixed)
        - model: Bus model (fixed)
        - operationalStatus: Current status (parked/charging/inTransit/inactive)
        - assignedRoute: Route this bus is assigned to
        - scheduledDeparture: When bus is scheduled to depart
        - avgConsumption: Average energy consumption per km
        """
        properties = {
            "batteryCapacity": self.battery_capacity,
            "model": self.model,
            "operationalStatus": self.operational_status,
            "assignedRoute": self.assigned_route,
            "scheduledDeparture": self.scheduled_departure,
            "avgConsumption": self.avg_consumption
        }
        
        try:
            # Update device twin in Azure
            await self.client.patch_twin_reported_properties(properties)
        except Exception as e:
            print(f"Error updating properties: {e}")
    
    async def send_telemetry(self):
        """
        Send real-time telemetry (sensor data) to Azure IoT Central.
        
        Called every 1 second to send current sensor readings.
        
        Telemetry includes:
        - batteryLevel: Battery state of charge as percentage
        - batteryKwh: Available battery energy in kWh
        - latitude/longitude: Current GPS position
        - instantConsumption: Current power draw (kW, negative when charging)
        - remainingRange: Estimated range in km based on current battery
        - batteryTemperature: Battery temperature in Celsius
        """
        telemetry = {
            "batteryLevel": round(self.battery_level, 2),
            "batteryKwh": round(self.battery_kwh, 2),
            "latitude": round(self.latitude, 6),  # 6 decimals for GPS precision
            "longitude": round(self.longitude, 6),
            "instantConsumption": round(self.instant_consumption, 2),
            "remainingRange": round(self.remaining_range, 2),
            "batteryTemperature": round(self.battery_temperature, 2)
        }
        
        # Create message
        message = Message(json.dumps(telemetry))
        message.content_type = "application/json"
        message.content_encoding = "utf-8"
        
        try:
            # Send to Azure
            await self.client.send_message(message)
        except Exception as e:
            print(f"Error sending telemetry: {e}")
    
    def update_state(self):
        """
        Update internal state based on current operational status.
        
        Simulates realistic behavior:
        - When charging: battery increases, temperature rises
        - When in transit: battery decreases, temperature rises, GPS changes
        - When parked: battery slowly self-discharges, temperature decreases
        
        Called every second before sending telemetry.
        """
        
        if self.operational_status == "charging":
            # Bus is connected to charger and receiving power
            
            # Only charge if battery is below 95% (stop charging at 95% to protect battery)
            if self.battery_level < 95:
                # Calculate energy gained per second
                # Charging power is in kW, divide by 3600 to get kWh per second
                # Apply 92% efficiency (8% lost as heat)
                energy_gain = (self.charging_power * 0.92) / 3600
                
                # Add energy to battery (cap at 95% of total capacity)
                self.battery_kwh = min(
                    self.battery_capacity * 0.95,
                    self.battery_kwh + energy_gain
                )
                
                # Update battery percentage
                self.battery_level = (self.battery_kwh / self.battery_capacity) * 100
                
                # Battery temperature increases when charging (capped at 40C)
                self.battery_temperature = min(
                    40.0,
                    self.battery_temperature + random.uniform(0.03, 0.08)
                )
                
                # Instant consumption is negative when charging (receiving power)
                self.instant_consumption = -self.charging_power
            else:
                # Fully charged, stop drawing power
                self.instant_consumption = 0.0
                
        elif self.operational_status == "inTransit":
            # Bus is driving on route
            
            # Simulate movement: assume average speed of 50 km/h
            # In 1 second at 50 km/h, bus travels approximately 0.014 km
            distance_per_second = 0.014  # km
            
            # Calculate energy consumed
            # Energy = distance * consumption rate / 3600 (to get kWh per second)
            energy_consumed = distance_per_second * self.avg_consumption / 3600
            
            # Reduce battery (minimum 0)
            self.battery_kwh = max(0, self.battery_kwh - energy_consumed)
            self.battery_level = (self.battery_kwh / self.battery_capacity) * 100
            
            # Instant consumption (power draw in kW at 50 km/h)
            # Consumption rate (kWh/km) * speed (km/h) = power (kW)
            self.instant_consumption = self.avg_consumption * 50
            
            # Battery temperature increases when driving (capped at 35C)
            self.battery_temperature = min(
                35.0,
                self.battery_temperature + random.uniform(0.02, 0.05)
            )
            
            # Simulate GPS movement (small random changes to lat/lon)
            self.latitude += random.uniform(-0.001, 0.001)
            self.longitude += random.uniform(-0.001, 0.001)
            
        elif self.operational_status == "parked":
            # Bus is parked (not charging, not moving)
            
            # Battery slowly self-discharges (very small amount)
            self.battery_kwh = max(0, self.battery_kwh - 0.0001)
            self.battery_level = (self.battery_kwh / self.battery_capacity) * 100
            
            # No power consumption when parked
            self.instant_consumption = 0.0
            
            # Temperature slowly returns to ambient (20C)
            self.battery_temperature = max(
                20.0,
                self.battery_temperature - random.uniform(0.01, 0.03)
            )
            
        else:  # inactive
            # Bus is inactive (maintenance, out of service, etc.)
            self.instant_consumption = 0.0
        
        # Update remaining range based on current battery and consumption rate
        # Range (km) = Available energy (kWh) / Consumption rate (kWh/km)
        if self.avg_consumption > 0:
            self.remaining_range = self.battery_kwh / self.avg_consumption
        else:
            self.remaining_range = 0
    
    async def start_charging(self, charger_id, power):
        """
        Start charging at a charging station.
        
        Args:
            charger_id: ID of charger connected to (e.g., "CS-001")
            power: Charging power allocated in kW (e.g., 80)
        
        Updates:
        - Changes status to "charging"
        - Records which charger is connected
        - Sets charging power
        - Updates properties in Azure
        """
        self.operational_status = "charging"
        self.connected_charger = charger_id
        self.charging_power = power
        
        # Notify Azure of status change
        await self.update_properties()
        
        print(f"{self.device_id} started charging at {charger_id} ({power} kW)")
    
    async def stop_charging(self):
        """
        Stop charging and return to parked status.
        
        Updates:
        - Changes status back to "parked"
        - Clears connected charger
        - Sets charging power to 0
        - Updates properties in Azure
        """
        print(f"{self.device_id} stopped charging (battery: {self.battery_level:.1f}%)")
        
        self.operational_status = "parked"
        self.connected_charger = None
        self.charging_power = 0.0
        
        # Notify Azure of status change
        await self.update_properties()
    
    async def start_route(self):
        """
        Start driving on assigned route.
        
        Updates:
        - Changes status to "inTransit"
        - Updates properties in Azure
        """
        self.operational_status = "inTransit"
        await self.update_properties()
        print(f"{self.device_id} departed for {self.assigned_route}")
    
    async def simulate(self):
        """
        Main simulation loop - runs forever.
        
        Every 1 second:
        1. Update internal state (battery, temperature, GPS, etc.)
        2. Send telemetry to Azure
        3. Sleep for 1 second
        4. Repeat
        
        This loop runs until the program is stopped (Ctrl+C).
        """
        while True:
            try:
                # Update state based on operational status
                self.update_state()
                
                # Send current telemetry to Azure
                await self.send_telemetry()
                
                # Wait 1 second before next iteration
                await asyncio.sleep(1)
                
            except Exception as e:
                # If error occurs, print it but keep running
                print(f"Error in simulation: {e}")
                await asyncio.sleep(1)
    
    async def disconnect(self):
        """
        Cleanly disconnect from Azure IoT Central.
        Called when program is stopping.
        """
        if self.client:
            await self.client.disconnect()