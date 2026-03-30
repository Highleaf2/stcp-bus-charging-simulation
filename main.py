import asyncio
from charging_station_simulator import ChargingStationSimulator
from electric_bus_simulator import ElectricBusSimulator
import config

charging_stations = {}
buses = {}

async def run_all_simulators():
    
    print("=" * 60)
    print("STCP Electric Bus Charging Simulation")
    print("=" * 60)
    print(f"Connecting {len(config.CHARGING_STATIONS)} charging stations...")
    print(f"Connecting {len(config.ELECTRIC_BUSES)} electric buses...")
    print("=" * 60)
    
    tasks = []
    
    for station_id, station_config in config.CHARGING_STATIONS.items():
        station = ChargingStationSimulator(
            device_id=station_config["device_id"],
            id_scope=config.ID_SCOPE,
            primary_key=station_config["primary_key"]
        )
        charging_stations[station_id] = station
        
        async def run_station(s):
            await s.connect()
            await s.simulate()
        
        tasks.append(asyncio.create_task(run_station(station)))
    
    for bus_id, bus_config in config.ELECTRIC_BUSES.items():
        bus = ElectricBusSimulator(
            device_id=bus_config["device_id"],
            id_scope=config.ID_SCOPE,
            primary_key=bus_config["primary_key"],
            route=bus_config["route"],
            departure_time=bus_config["departure_time"],
            station_location=config.STATION_LOCATION
        )
        buses[bus_id] = bus
        
        async def run_bus(b):
            await b.connect()
            await b.simulate()
        
        tasks.append(asyncio.create_task(run_bus(bus)))
    
    print("\nAll simulators started")
    print(f"Sending telemetry every {config.TELEMETRY_INTERVAL} second(s)")
    print("\nPress Ctrl+C to stop\n")
    
    try:
        await asyncio.gather(*tasks)
    except KeyboardInterrupt:
        print("\n\n--- Stopping all simulators ---")
        for station in charging_stations.values():
            await station.disconnect()
        for bus in buses.values():
            await bus.disconnect()
        print("All simulators stopped")


def main():
    if config.ID_SCOPE == "your-id-scope-here":
        print("=" * 60)
        print("ERROR: Please configure your Azure IoT Central credentials")
        print("=" * 60)
        return
    
    try:
        asyncio.run(run_all_simulators())
    except asyncio.TimeoutError:
        print("\nSimulacao terminada apos 60 segundos")
    except KeyboardInterrupt:
        print("\nShutdown requested")


if __name__ == "__main__":
    main()