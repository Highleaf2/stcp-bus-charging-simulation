import asyncio
import json
import random
from datetime import datetime
from azure.iot.device.aio import IoTHubDeviceClient, ProvisioningDeviceClient
from azure.iot.device import Message

class ChargingStationSimulator:
    
    def __init__(self, device_id, id_scope, primary_key):
        self.device_id = device_id
        self.id_scope = id_scope
        self.primary_key = primary_key
        self.client = None
        
        self.status = "available"
        self.max_power = 120.0
        self.current_power = 0.0
        self.charger_temperature = 22.0
        self.energy_delivered = 0.0
        self.current_efficiency = 92.0
        self.connected_bus_id = None
        self.charging_start_time = None
        self.cost_per_kwh = 0.15

        station_coords = {
            "CS-001": {"latitude": 41.152661, "longitude": -8.579658},
            "CS-002": {"latitude": 41.152671, "longitude": -8.579668},
            "CS-003": {"latitude": 41.152681, "longitude": -8.579678}
        }
        self.latitude = station_coords.get(device_id, {}).get("latitude", 41.152661)
        self.longitude = station_coords.get(device_id, {}).get("longitude", -8.579658)

    async def provision_device(self):
        provisioning_client = ProvisioningDeviceClient.create_from_symmetric_key(
            provisioning_host="global.azure-devices-provisioning.net",
            registration_id=self.device_id,
            id_scope=self.id_scope,
            symmetric_key=self.primary_key
        )
        registration_result = await provisioning_client.register()
        if registration_result.status == "assigned":
            return registration_result.registration_state.assigned_hub
        else:
            raise RuntimeError(f"Registration failed: {registration_result.status}")
    
    async def connect(self):
        try:
            assigned_hub = await self.provision_device()
            conn_str = f"HostName={assigned_hub};DeviceId={self.device_id};SharedAccessKey={self.primary_key}"
            self.client = IoTHubDeviceClient.create_from_connection_string(conn_str)
            await self.client.connect()
            print(f"Connected: {self.device_id}")
            await self.update_properties()
        except Exception as e:
            print(f"Error connecting {self.device_id}: {e}")
            raise
    
    async def update_properties(self):
        properties = {
            "status": self.status,
            "maxPower": self.max_power,
            "connectedBusId": self.connected_bus_id,
            "chargingStartTime": self.charging_start_time,
            "costPerKwh": self.cost_per_kwh
        }
        try:
            await self.client.patch_twin_reported_properties(properties)
        except Exception as e:
            print(f"Error updating properties: {e}")
    
    async def send_telemetry(self):
        telemetry = {
            "currentPower": round(self.current_power, 2),
            "chargerTemperature": round(self.charger_temperature, 2),
            "energyDelivered": round(self.energy_delivered, 2),
            "currentEfficiency": round(self.current_efficiency, 2),
            "state": self.status,
            "connectedBus": self.connected_bus_id,
            "latitude": self.latitude,
            "longitude": self.longitude
        }
        message = Message(json.dumps(telemetry))
        message.content_type = "application/json"
        message.content_encoding = "utf-8"
        try:
            await self.client.send_message(message)
        except Exception as e:
            print(f"Error sending telemetry: {e}")
    
    def update_state(self):
        if self.status == "occupied" and self.connected_bus_id:
            self.charger_temperature = min(45.0, self.charger_temperature + random.uniform(0.05, 0.15))
            energy_per_second = self.current_power / 3600
            self.energy_delivered += energy_per_second
            self.current_efficiency = 92.0 + random.uniform(-1.0, 1.0)
        elif self.status == "available":
            self.current_power = 0.0
            self.charger_temperature = max(22.0, self.charger_temperature - random.uniform(0.02, 0.08))
            self.current_efficiency = 92.0
    
    async def start_charging(self, bus_id, power_allocation):
        self.status = "occupied"
        self.connected_bus_id = bus_id
        self.current_power = power_allocation
        self.charging_start_time = datetime.utcnow().isoformat()
        await self.update_properties()
        print(f"{self.device_id} charging {bus_id} at {power_allocation} kW")
    
    async def stop_charging(self):
        print(f"{self.device_id} stopped charging")
        self.status = "available"
        self.connected_bus_id = None
        self.current_power = 0.0
        self.charging_start_time = None
        await self.update_properties()
    
    async def simulate(self):
        while True:
            try:
                self.update_state()
                await self.send_telemetry()
                await asyncio.sleep(1)
            except Exception as e:
                print(f"Error in simulation: {e}")
                await asyncio.sleep(1)
    
    async def disconnect(self):
        if self.client:
            await self.client.disconnect()