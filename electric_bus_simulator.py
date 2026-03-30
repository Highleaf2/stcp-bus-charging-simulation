import asyncio
import json
import random
from datetime import datetime
from azure.iot.device.aio import IoTHubDeviceClient, ProvisioningDeviceClient
from azure.iot.device import Message

class ElectricBusSimulator:
    
    def __init__(self, device_id, id_scope, primary_key, route, departure_time, station_location):
        self.device_id = device_id
        self.id_scope = id_scope
        self.primary_key = primary_key
        self.client = None
        
        self.battery_capacity = 350.0
        self.model = "CaetanoBus e.City Gold"
        self.assigned_route = route
        self.scheduled_departure = departure_time
        self.avg_consumption = 1.2

        bus_config = {
            "BUS-001": {"battery_level": 45.0, "status": "inTransit"},
            "BUS-002": {"battery_level": 70.0, "status": "inTransit"},
            "BUS-003": {"battery_level": 25.0, "status": "inTransit"}
        }

        config = bus_config.get(device_id, {"battery_level": 50.0, "status": "parked"})
        self.operational_status = config["status"]
        self.battery_level = config["battery_level"]
        self.battery_kwh = (self.battery_level / 100) * self.battery_capacity
        self.latitude = station_location["latitude"]
        self.longitude = station_location["longitude"]
        self.instant_consumption = 0.0
        self.remaining_range = self.battery_kwh / self.avg_consumption
        self.battery_temperature = random.uniform(18, 25)
        self.connected_charger = None
        self.charging_power = 0.0
        
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
            "batteryCapacity": self.battery_capacity,
            "model": self.model,
            "operationalStatus": self.operational_status,
            "assignedRoute": self.assigned_route,
            "scheduledDeparture": self.scheduled_departure,
            "avgConsumption": self.avg_consumption
        }
        try:
            await self.client.patch_twin_reported_properties(properties)
        except Exception as e:
            print(f"Error updating properties: {e}")
    
    async def send_telemetry(self):
        telemetry = {
            "batteryLevel": round(self.battery_level, 2),
            "batteryKwh": round(self.battery_kwh, 2),
            "latitude": round(self.latitude, 6),
            "longitude": round(self.longitude, 6),
            "batteryTemperature": round(self.battery_temperature, 2),
            "instantConsumption": round(self.instant_consumption, 2),
            "remainingRange": round(self.remaining_range, 2),
            "state": self.operational_status
        }
        message = Message(json.dumps(telemetry))
        message.content_type = "application/json"
        message.content_encoding = "utf-8"
        try:
            await self.client.send_message(message)
        except Exception as e:
            print(f"Error sending telemetry: {e}")
    
    def update_state(self):
        if self.operational_status == "charging":
            if self.battery_level < 95:
                energy_gain = (self.charging_power * 0.92) / 3600
                self.battery_kwh = min(self.battery_capacity * 0.95, self.battery_kwh + energy_gain)
                self.battery_level = (self.battery_kwh / self.battery_capacity) * 100
                self.battery_temperature = min(40.0, self.battery_temperature + random.uniform(0.03, 0.08))
                self.instant_consumption = -self.charging_power
            else:
                self.instant_consumption = 0.0
                
        elif self.operational_status == "inTransit":
            distance_per_second = 15
            energy_consumed = distance_per_second * self.avg_consumption / 3600
            self.battery_kwh = max(0, self.battery_kwh - energy_consumed)
            self.battery_level = (self.battery_kwh / self.battery_capacity) * 100
            self.instant_consumption = self.avg_consumption * 50
            self.battery_temperature = min(35.0, self.battery_temperature + random.uniform(0.02, 0.05))
            self.latitude += random.uniform(-0.001, 0.001)
            self.longitude += random.uniform(-0.001, 0.001)
            
        elif self.operational_status == "parked":
            self.battery_kwh = max(0, self.battery_kwh - 0.0001)
            self.battery_level = (self.battery_kwh / self.battery_capacity) * 100
            self.instant_consumption = 0.0
            self.battery_temperature = max(20.0, self.battery_temperature - random.uniform(0.01, 0.03))

        if self.avg_consumption > 0:
            self.remaining_range = self.battery_kwh / self.avg_consumption
        else:
            self.remaining_range = 0
    
    async def start_charging(self, charger_id, power):
        self.operational_status = "charging"
        self.connected_charger = charger_id
        self.charging_power = power
        await self.update_properties()
        print(f"{self.device_id} started charging at {charger_id} ({power} kW)")
    
    async def stop_charging(self):
        print(f"{self.device_id} stopped charging (battery: {self.battery_level:.1f}%)")
        self.operational_status = "parked"
        self.connected_charger = None
        self.charging_power = 0.0
        await self.update_properties()
    
    async def start_route(self):
        self.operational_status = "inTransit"
        await self.update_properties()
        print(f"{self.device_id} departed for {self.assigned_route}")
    
    async def simulate(self):
        while True:
            try:
                self.update_state()
                await self.send_telemetry()
                await asyncio.sleep(5)
            except Exception as e:
                print(f"Error in simulation: {e}")
                await asyncio.sleep(5)
    
    async def disconnect(self):
        if self.client:
            await self.client.disconnect()