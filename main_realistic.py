"""
STCP Bus Charging Simulation - Coordinated Scenario
Orchestrates realistic bus and charger behavior
"""

import asyncio
import json
import random
from datetime import datetime
from azure.iot.device.aio import IoTHubDeviceClient, ProvisioningDeviceClient
from azure.iot.device import Message, MethodResponse
from bus_simulator import BusSimulator, BusState
from charger_simulator import ChargerSimulator
import config

# Azure IoT Central Configuration from config.py
ID_SCOPE = config.ID_SCOPE

# Device IDs
BUS_IDS = list(config.ELECTRIC_BUSES.keys())
CHARGER_IDS = list(config.CHARGING_STATIONS.keys())

# Simulation parameters
TELEMETRY_INTERVAL_SECONDS = config.TELEMETRY_INTERVAL
SCENARIO_UPDATE_INTERVAL_SECONDS = 10

class SimulationCoordinator:
    """
    Coordinates realistic simulation scenarios:
    - Morning charging session
    - Day operations (routes)
    - Evening return and charging
    """
    
    def __init__(self):
        self.buses = {}
        self.chargers = {}
        self.clients = {}
        self.simulation_time = 0  # Simulated time in seconds
        
        # Scenario state
        self.current_scenario = "MORNING_CHARGING"
        self.scenario_start_time = 0
    
    async def provision_device(self, device_id, model_id):
        """Provision device with Azure IoT Central"""
        provisioning_host = "global.azure-devices-provisioning.net"
        
        # Get device-specific key from config
        if device_id in config.ELECTRIC_BUSES:
            device_key = config.ELECTRIC_BUSES[device_id]["primary_key"]
        elif device_id in config.CHARGING_STATIONS:
            device_key = config.CHARGING_STATIONS[device_id]["primary_key"]
        else:
            raise Exception(f"Unknown device: {device_id}")
        
        provisioning_client = ProvisioningDeviceClient.create_from_symmetric_key(
            provisioning_host=provisioning_host,
            registration_id=device_id,
            id_scope=ID_SCOPE,
            symmetric_key=device_key,
        )
        
        provisioning_client.provisioning_payload = json.dumps({"modelId": model_id})
        
        registration_result = await provisioning_client.register()
        
        if registration_result.status == "assigned":
            device_client = IoTHubDeviceClient.create_from_symmetric_key(
                symmetric_key=device_key,
                hostname=registration_result.registration_state.assigned_hub,
                device_id=device_id,
            )
            await device_client.connect()
            print(f"✓ [{device_id}] Connected to IoT Central")
            return device_client
        else:
            raise Exception(f"Device {device_id} registration failed: {registration_result.status}")
    
    async def initialize_devices(self):
        """Initialize all buses and chargers"""
        print("\n" + "="*60)
        print("STCP SIMULATION - REALISTIC VERSION")
        print("="*60)
        
        # Initialize buses with different starting battery levels
        initial_batteries = [66, 61, 55]  # Different levels for each bus
        for i, bus_id in enumerate(BUS_IDS):
            self.buses[bus_id] = BusSimulator(bus_id, initial_batteries[i])
            
            # Provision device
            model_id = "dtmi:nv2r8wn:dzaeymsn"  # Your bus model ID
            self.clients[bus_id] = await self.provision_device(bus_id, model_id)
        
        # Initialize chargers
        for charger_id in CHARGER_IDS:
            self.chargers[charger_id] = ChargerSimulator(charger_id)
            
            # Provision device
            model_id = "dtmi:uo6xyxu9:m8hczfdfd"  # Your charger model ID
            self.clients[charger_id] = await self.provision_device(charger_id, model_id)
        
        print("\n✓ All devices initialized and connected\n")
    
    def _update_scenario(self):
        """Update simulation scenario based on time"""
        scenario_time = self.simulation_time - self.scenario_start_time
        
        # SCENARIO 1: MORNING CHARGING (0-30 min)
        if self.current_scenario == "MORNING_CHARGING":
            if scenario_time < 30 * 60:
                # All buses charging
                for i, bus_id in enumerate(BUS_IDS):
                    bus = self.buses[bus_id]
                    if bus.state != BusState.CHARGING and bus.battery_percent < 90:
                        charger_id = CHARGER_IDS[i]
                        charger = self.chargers[charger_id]
                        
                        if charger.connect_bus(bus_id):
                            bus.start_charging(charger_id, 150)
            else:
                # Transition to OPERATIONS
                print("\n>>> SCENARIO CHANGE: OPERATIONS <<<\n")
                self.current_scenario = "OPERATIONS"
                self.scenario_start_time = self.simulation_time
                
                # Stop all charging
                for bus_id in BUS_IDS:
                    bus = self.buses[bus_id]
                    if bus.state == BusState.CHARGING:
                        bus.stop_charging()
                        
                for charger_id in CHARGER_IDS:
                    self.chargers[charger_id].disconnect_bus()
        
        # SCENARIO 2: OPERATIONS (30-90 min)
        elif self.current_scenario == "OPERATIONS":
            if scenario_time < 60 * 60:
                # Buses on routes with occasional stops
                for bus_id in BUS_IDS:
                    bus = self.buses[bus_id]
                    
                    if bus.state == BusState.IDLE_DEPOT:
                        bus.start_route()
                    elif bus.state == BusState.ROUTE:
                        # Random stop at station
                        if random.random() < 0.1:  # 10% chance per update
                            bus.stop_at_station()
                    elif bus.state == BusState.IDLE_ON_ROUTE:
                        # Resume after ~20 seconds
                        if bus.time_in_state > 20:
                            bus.start_route()
            else:
                # Transition to EVENING RETURN
                print("\n>>> SCENARIO CHANGE: EVENING RETURN <<<\n")
                self.current_scenario = "EVENING_RETURN"
                self.scenario_start_time = self.simulation_time
                
                # All buses return to depot
                for bus_id in BUS_IDS:
                    self.buses[bus_id].return_to_depot()
        
        # SCENARIO 3: EVENING RETURN (90-120 min)
        elif self.current_scenario == "EVENING_RETURN":
            if scenario_time < 30 * 60:
                # Start charging if battery < 80%
                for i, bus_id in enumerate(BUS_IDS):
                    bus = self.buses[bus_id]
                    if bus.state == BusState.IDLE_DEPOT and bus.battery_percent < 80:
                        charger_id = CHARGER_IDS[i]
                        charger = self.chargers[charger_id]
                        
                        if charger.connect_bus(bus_id):
                            bus.start_charging(charger_id, 150)
            else:
                # Simulation complete - reset
                print("\n>>> SCENARIO COMPLETE - RESTARTING <<<\n")
                self.current_scenario = "MORNING_CHARGING"
                self.scenario_start_time = self.simulation_time
    
    async def send_telemetry(self, device_id, telemetry):
        """Send telemetry to IoT Central"""
        try:
            client = self.clients[device_id]
            message = Message(json.dumps(telemetry))
            message.content_encoding = "utf-8"
            message.content_type = "application/json"
            await client.send_message(message)
        except Exception as e:
            print(f"✗ [{device_id}] Error sending telemetry: {e}")
    
    async def update_loop(self):
        """Main update loop"""
        while True:
            try:
                # Update simulation time
                self.simulation_time += SCENARIO_UPDATE_INTERVAL_SECONDS
                
                # Update scenario
                self._update_scenario()
                
                # Update all devices
                for bus_id in BUS_IDS:
                    bus = self.buses[bus_id]
                    bus.update()
                    
                    # Update charger power if charging
                    if bus.state == BusState.CHARGING and bus.connected_charger_id:
                        charger = self.chargers[bus.connected_charger_id]
                        power = charger.set_charging_power(150, bus.battery_percent)
                
                for charger_id in CHARGER_IDS:
                    self.chargers[charger_id].update()
                
                # Send telemetry
                for bus_id in BUS_IDS:
                    telemetry = self.buses[bus_id].get_telemetry()
                    await self.send_telemetry(bus_id, telemetry)
                    
                    # Log status periodically
                    if self.simulation_time % 30 == 0:
                        print(f"[{bus_id}] {telemetry['state']} - "
                              f"Battery: {telemetry['batteryLevel']:.1f}% ({telemetry['batteryKwh']:.1f} kWh) - "
                              f"Temp: {telemetry['batteryTemperature']:.1f}°C - "
                              f"Location: ({telemetry['latitude']:.4f}, {telemetry['longitude']:.4f})")
                
                for charger_id in CHARGER_IDS:
                    telemetry = self.chargers[charger_id].get_telemetry()
                    await self.send_telemetry(charger_id, telemetry)
                    
                    if self.simulation_time % 30 == 0 and telemetry['currentPower'] > 0:
                        print(f"[{charger_id}] {telemetry['state']} - "
                              f"Power: {telemetry['currentPower']:.1f} kW - "
                              f"Energy: {telemetry['energyDelivered']:.1f} kWh")
                
                await asyncio.sleep(SCENARIO_UPDATE_INTERVAL_SECONDS)
                
            except Exception as e:
                print(f"✗ Error in update loop: {e}")
                await asyncio.sleep(5)
    
    async def run(self):
        """Run simulation"""
        try:
            await self.initialize_devices()
            print("\n>>> Starting simulation with realistic scenarios <<<")
            print(f">>> Telemetry every {TELEMETRY_INTERVAL_SECONDS}s, Updates every {SCENARIO_UPDATE_INTERVAL_SECONDS}s <<<\n")
            
            await self.update_loop()
            
        except KeyboardInterrupt:
            print("\n\nSimulation stopped by user")
        except Exception as e:
            print(f"\n✗ Simulation error: {e}")
        finally:
            # Disconnect all clients
            for device_id, client in self.clients.items():
                try:
                    await client.disconnect()
                    print(f"✓ [{device_id}] Disconnected")
                except:
                    pass

async def main():
    """Main entry point"""
    coordinator = SimulationCoordinator()
    await coordinator.run()

if __name__ == "__main__":
    asyncio.run(main())