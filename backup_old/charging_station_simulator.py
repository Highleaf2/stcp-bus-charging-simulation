# charging_station_simulator.py
# Simulates a charging station that sends telemetry to Azure IoT Central

import asyncio
import json
import random
from datetime import datetime
from azure.iot.device.aio import IoTHubDeviceClient, ProvisioningDeviceClient
from azure.iot.device import Message

class ChargingStationSimulator:
    """
    Represents a single charging station device.
    Manages connection to Azure IoT Central and simulates charging behavior.
    """
    
    def __init__(self, device_id, id_scope, primary_key):
        """
        Initialize the charging station with Azure credentials and initial state.
        
        Args:
            device_id: Unique identifier (e.g., "CS-001")
            id_scope: Azure IoT Central application ID scope
            primary_key: Authentication key from Azure IoT Central
        """
        # Azure connection parameters
        self.device_id = device_id
        self.id_scope = id_scope
        self.primary_key = primary_key
        self.client = None  # Will hold the Azure IoT Hub client once connected
        
        # Charging station state variables
        self.status = "available"  # Can be: available, occupied, inactive, maintenance
        self.max_power = 120.0  # Maximum power capacity in kW
        self.current_power = 0.0  # Current power being delivered in kW
        self.charger_temperature = 22.0  # Temperature of charging equipment in Celsius
        self.energy_delivered = 0.0  # Cumulative energy delivered in kWh
        self.current_efficiency = 92.0  # Charging efficiency as percentage
        self.connected_bus_id = None  # ID of connected bus, None if no bus connected
        self.charging_start_time = None  # ISO timestamp when charging started
        self.cost_per_kwh = 0.15  # Cost per kilowatt-hour in euros
        
    async def provision_device(self):
        """
        Register this device with Azure IoT Central using DPS (Device Provisioning Service).
        DPS assigns the device to the correct IoT Hub dynamically.
        
        Returns:
            String with the assigned IoT Hub hostname
            
        Raises:
            RuntimeError if registration fails
        """
        # Create a provisioning client with our credentials
        provisioning_client = ProvisioningDeviceClient.create_from_symmetric_key(
            provisioning_host="global.azure-devices-provisioning.net",  # Global DPS endpoint
            registration_id=self.device_id,  # Use device ID as registration ID
            id_scope=self.id_scope,  # Application scope from Azure IoT Central
            symmetric_key=self.primary_key  # Authentication key
        )
        
        # Register with Azure - this happens asynchronously
        registration_result = await provisioning_client.register()
        
        # Check if registration was successful
        if registration_result.status == "assigned":
            # Return the IoT Hub hostname we were assigned to
            return registration_result.registration_state.assigned_hub
        else:
            # Registration failed - raise error
            raise RuntimeError(f"Registration failed: {registration_result.status}")
    
    async def connect(self):
        """
        Establish connection to Azure IoT Central.
        
        Steps:
        1. Provision device to get IoT Hub assignment
        2. Build connection string
        3. Create IoT Hub client
        4. Connect to Azure
        5. Send initial properties
        """
        try:
            # Step 1: Get assigned IoT Hub hostname via DPS
            assigned_hub = await self.provision_device()
            
            # Step 2: Build connection string with format:
            # HostName=<hub>;DeviceId=<id>;SharedAccessKey=<key>
            conn_str = f"HostName={assigned_hub};DeviceId={self.device_id};SharedAccessKey={self.primary_key}"
            
            # Step 3: Create IoT Hub client from connection string
            self.client = IoTHubDeviceClient.create_from_connection_string(conn_str)
            
            # Step 4: Connect to Azure IoT Central
            await self.client.connect()
            print(f"Connected: {self.device_id}")
            
            # Step 5: Send initial device properties (status, max power, etc.)
            await self.update_properties()
            
        except Exception as e:
            # If any step fails, print error and re-raise exception
            print(f"Error connecting {self.device_id}: {e}")
            raise
    
    async def update_properties(self):
        """
        Update device twin properties in Azure IoT Central.
        
        Properties are semi-static data that describes the device (not real-time telemetry).
        These are updated only when values change, not every second.
        
        Properties sent:
        - status: Current operational status
        - maxPower: Maximum power capacity
        - connectedBusId: Which bus is connected (or None)
        - chargingStartTime: When current charging session started
        - costPerKwh: Cost per kilowatt-hour
        """
        # Build properties dictionary
        properties = {
            "status": self.status,
            "maxPower": self.max_power,
            "connectedBusId": self.connected_bus_id,
            "chargingStartTime": self.charging_start_time,
            "costPerKwh": self.cost_per_kwh
        }
        
        try:
            # Send properties to Azure via device twin reported properties
            await self.client.patch_twin_reported_properties(properties)
        except Exception as e:
            print(f"Error updating properties: {e}")
    
    async def send_telemetry(self):
        """
        Send real-time telemetry (sensor data) to Azure IoT Central.
        
        This is called every 1 second to send current sensor readings.
        
        Telemetry includes:
        - currentPower: Power being delivered right now (kW)
        - chargerTemperature: Current temperature (Celsius)
        - energyDelivered: Total energy delivered since start (kWh)
        - currentEfficiency: Current charging efficiency (%)
        """
        # Build telemetry dictionary with current sensor values
        telemetry = {
            "currentPower": round(self.current_power, 2),
            "chargerTemperature": round(self.charger_temperature, 2),
            "energyDelivered": round(self.energy_delivered, 2),
            "currentEfficiency": round(self.current_efficiency, 2)
        }
        
        # Create Azure IoT message from JSON
        message = Message(json.dumps(telemetry))
        message.content_type = "application/json"  # Tell Azure this is JSON
        message.content_encoding = "utf-8"  # Character encoding
        
        try:
            # Send message to Azure IoT Central
            await self.client.send_message(message)
        except Exception as e:
            print(f"Error sending telemetry: {e}")
    
    def update_state(self):
        """
        Update internal state based on current status.
        
        This simulates realistic behavior:
        - When charging: temperature increases, energy accumulates
        - When idle: temperature decreases back to ambient
        
        Called every second before sending telemetry.
        """
        if self.status == "occupied" and self.connected_bus_id:
            # Station is actively charging a bus
            
            # Temperature increases when charging (but capped at 45C)
            self.charger_temperature = min(
                45.0, 
                self.charger_temperature + random.uniform(0.05, 0.15)
            )
            
            # Calculate energy delivered in this second
            # Power is in kW, divide by 3600 to get kWh per second
            energy_per_second = self.current_power / 3600
            self.energy_delivered += energy_per_second
            
            # Efficiency varies slightly around 92%
            self.current_efficiency = 92.0 + random.uniform(-1.0, 1.0)
            
        elif self.status == "available":
            # Station is idle (not charging)
            
            # No power being delivered
            self.current_power = 0.0
            
            # Temperature slowly returns to ambient (22C)
            self.charger_temperature = max(
                22.0, 
                self.charger_temperature - random.uniform(0.02, 0.08)
            )
            
            # Efficiency at nominal value when idle
            self.current_efficiency = 92.0
    
    async def start_charging(self, bus_id, power_allocation):
        """
        Start charging a bus.
        
        Args:
            bus_id: ID of the bus connecting (e.g., "BUS-001")
            power_allocation: Power to allocate in kW (e.g., 80)
        
        Updates:
        - Changes status to "occupied"
        - Records which bus is connected
        - Sets current power output
        - Records start time
        - Updates properties in Azure
        """
        self.status = "occupied"
        self.connected_bus_id = bus_id
        self.current_power = power_allocation
        self.charging_start_time = datetime.utcnow().isoformat()  # ISO format timestamp
        
        # Notify Azure of status change
        await self.update_properties()
        
        print(f"{self.device_id} charging {bus_id} at {power_allocation} kW")
    
    async def stop_charging(self):
        """
        Stop charging and return to available status.
        
        Updates:
        - Changes status back to "available"
        - Clears connected bus
        - Sets power to 0
        - Clears start time
        - Updates properties in Azure
        """
        print(f"{self.device_id} stopped charging")
        
        self.status = "available"
        self.connected_bus_id = None
        self.current_power = 0.0
        self.charging_start_time = None
        
        # Notify Azure of status change
        await self.update_properties()
    
    async def simulate(self):
        """
        Main simulation loop - runs forever.
        
        Every 1 second:
        1. Update internal state (temperature, energy, etc.)
        2. Send telemetry to Azure
        3. Sleep for 1 second
        4. Repeat
        
        This loop runs until the program is stopped (Ctrl+C).
        """
        while True:
            try:
                # Update state based on current status
                self.update_state()
                
                # Send current telemetry to Azure
                await self.send_telemetry()
                
                # Wait 1 second before next iteration (1 event per second requirement)
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