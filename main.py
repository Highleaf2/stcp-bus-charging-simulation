# main.py
# Main orchestrator - runs all 6 devices (3 charging stations + 3 buses) in parallel
# Implements simple charging logic that connects buses to available chargers

import asyncio
from charging_station_simulator import ChargingStationSimulator
from electric_bus_simulator import ElectricBusSimulator
import config

# Global dictionaries to store simulator instances
# This allows different async tasks to access and control each device
charging_stations = {}  # Key: "CS-001", Value: ChargingStationSimulator instance
buses = {}  # Key: "BUS-001", Value: ElectricBusSimulator instance

async def simple_charging_orchestrator():
    """
    Simple orchestration logic that manages charging sessions.
    
    This is a basic version - later you'll implement the full optimization algorithm.
    
    Logic:
    - If bus battery < 50% and parked -> connect to available charger
    - If bus battery >= 90% and charging -> disconnect
    
    Runs every 5 seconds to check and adjust charging.
    """
    # Wait 10 seconds for all devices to connect first
    await asyncio.sleep(10)
    
    print("\n--- Charging Orchestrator Started ---")
    
    # Infinite loop - runs until program stops
    while True:
        try:
            # Wait 5 seconds between checks (don't need to check every second)
            await asyncio.sleep(5)
            
            # Check each bus
            for bus_id, bus in buses.items():
                
                # Rule 1: If bus needs charging (< 50%) and is parked
                if bus.battery_level < 50 and bus.operational_status == "parked":
                    
                    # Find an available charging station
                    for station_id, station in charging_stations.items():
                        
                        if station.status == "available":
                            # Found available charger
                            # Allocate 80 kW charging power (simple fixed allocation)
                            await station.start_charging(bus_id, 80.0)
                            await bus.start_charging(station_id, 80.0)
                            break  # Stop looking for chargers once connected
                
                # Rule 2: If bus is sufficiently charged (>= 90%), disconnect
                elif bus.battery_level >= 90 and bus.operational_status == "charging":
                    
                    # Get which charger this bus is connected to
                    charger_id = bus.connected_charger
                    
                    # Disconnect both bus and charger
                    if charger_id and charger_id in charging_stations:
                        await charging_stations[charger_id].stop_charging()
                        await bus.stop_charging()
                        
        except Exception as e:
            print(f"Error in orchestrator: {e}")


async def run_all_simulators():
    """
    Start all 6 simulators in parallel and orchestrate charging.
    
    Creates async tasks for:
    - 3 charging stations (each runs independently)
    - 3 electric buses (each runs independently)
    - 1 orchestrator (manages charging connections)
    
    All tasks run concurrently using asyncio.
    """
    
    # Print header
    print("=" * 60)
    print("STCP Electric Bus Charging Simulation")
    print("=" * 60)
    print(f"Connecting {len(config.CHARGING_STATIONS)} charging stations...")
    print(f"Connecting {len(config.ELECTRIC_BUSES)} electric buses...")
    print("=" * 60)
    
    # List to hold all async tasks
    tasks = []
    
    # Create charging station simulators
    for station_id, station_config in config.CHARGING_STATIONS.items():
        
        # Create simulator instance
        station = ChargingStationSimulator(
            device_id=station_config["device_id"],
            id_scope=config.ID_SCOPE,
            primary_key=station_config["primary_key"]
        )
        
        # Store in global dictionary so orchestrator can access it
        charging_stations[station_id] = station
        
        # Define async function to run this station
        async def run_station(s):
            await s.connect()  # Connect to Azure
            await s.simulate()  # Start simulation loop
        
        # Create task and add to list
        tasks.append(asyncio.create_task(run_station(station)))
    
    # Create electric bus simulators
    for bus_id, bus_config in config.ELECTRIC_BUSES.items():
        
        # Create simulator instance
        bus = ElectricBusSimulator(
            device_id=bus_config["device_id"],
            id_scope=config.ID_SCOPE,
            primary_key=bus_config["primary_key"],
            route=bus_config["route"],
            departure_time=bus_config["departure_time"],
            station_location=config.STATION_LOCATION
        )
        
        # Store in global dictionary
        buses[bus_id] = bus
        
        # Define async function to run this bus
        async def run_bus(b):
            await b.connect()  # Connect to Azure
            await b.simulate()  # Start simulation loop
        
        # Create task and add to list
        tasks.append(asyncio.create_task(run_bus(bus)))
    
    # Add orchestrator task
    tasks.append(asyncio.create_task(simple_charging_orchestrator()))
    
    print("\nAll simulators started")
    print(f"Sending telemetry every {config.TELEMETRY_INTERVAL} second(s)")
    print("\nPress Ctrl+C to stop\n")
    
    # Run all tasks concurrently
    # This will run until Ctrl+C or an error occurs
    try:
        await asyncio.gather(*tasks)
    except KeyboardInterrupt:
        # User pressed Ctrl+C
        print("\n\n--- Stopping all simulators ---")
        
        # Disconnect all devices cleanly
        for station in charging_stations.values():
            await station.disconnect()
        for bus in buses.values():
            await bus.disconnect()
        
        print("All simulators stopped")


def main():
    """
    Main entry point of the program.
    
    Checks if config is properly filled, then starts async event loop.
    """
    
    # Check if user has configured Azure credentials
    if config.ID_SCOPE == "your-id-scope-here":
        print("=" * 60)
        print("ERROR: Please configure your Azure IoT Central credentials")
        print("=" * 60)
        print("\nEdit config.py and fill in:")
        print("  - ID_SCOPE")
        print("  - Primary keys for all 6 devices")
        print("\nOr create .env file with credentials")
        print("=" * 60)
        return
    
    # Run the async main function
    try:
        # asyncio.run() starts the event loop and runs the async function
        asyncio.run(run_all_simulators())
    except KeyboardInterrupt:
        # Handle Ctrl+C gracefully
        print("\nShutdown requested")


# Python entry point
# This code only runs when you execute: python main.py
# It does NOT run when you import this file from another file
if __name__ == "__main__":
    main()