"""
STCP Bus Charging Simulation - Cenário GTFS Real
Simula cenário real baseado em rotas e estados fornecidos
"""

import asyncio
import json
from datetime import datetime
from azure.iot.device.aio import IoTHubDeviceClient, ProvisioningDeviceClient
from azure.iot.device import Message
from bus_simulator_gtfs import BusSimulatorGTFS
from charger_simulator import ChargerSimulator
from charging_scheduler import ChargingScheduler
import gtfs_routes
import config

# IDs dos dispositivos
BUS_IDS = ["BUS-001", "BUS-002", "BUS-003"]
CHARGER_IDS = ["CS-001", "CS-002", "CS-003"]

# Intervalo de atualização (segundos)
UPDATE_INTERVAL_SECONDS = 5
TELEMETRY_INTERVAL_SECONDS = 5

class GTFSSimulationCoordinator:
    """
    Coordenador de simulação com rotas GTFS reais
    """
    
    def __init__(self):
        self.buses = {}
        self.chargers = {}
        self.clients = {}
        self.simulation_time = 0
        
        # Algoritmo de otimização
        self.scheduler = ChargingScheduler()
        self.last_optimization_time = 0
        self.optimization_interval = 30  # Executar a cada 30s
    
    async def provision_device(self, device_id, model_id):
        """Provisionar dispositivo no Azure IoT Central via DPS"""
        try:
            # Obter chave específica do dispositivo
            device_key = config.get_device_key(device_id)
            
            provisioning_client = ProvisioningDeviceClient.create_from_symmetric_key(
                provisioning_host=config.PROVISIONING_HOST,
                registration_id=device_id,
                id_scope=config.ID_SCOPE,
                symmetric_key=device_key
            )
            
            print(f"[{device_id}] A registar dispositivo...")
            registration_result = await provisioning_client.register()
            
            if registration_result.status == "assigned":
                print(f"[{device_id}] ✓ Registado com sucesso")
                
                # Criar cliente IoT Hub
                conn_str = f"HostName={registration_result.registration_state.assigned_hub};DeviceId={device_id};SharedAccessKey={device_key}"
                client = IoTHubDeviceClient.create_from_connection_string(conn_str)
                await client.connect()
                
                return client
            else:
                print(f"[{device_id}] ✗ Registo falhou: {registration_result.status}")
                return None
                
        except Exception as e:
            print(f"[{device_id}] ✗ Erro no provisionamento: {e}")
            return None
    
    async def initialize_devices(self):
        """Inicializar todos os autocarros e estações"""
        print("\n" + "="*80)
        print("STCP SIMULATION - CENÁRIO GTFS REAL")
        print("Rotas reais do Porto com estados iniciais específicos")
        print("="*80)
        
        # Inicializar autocarros com estados GTFS
        for bus_id in BUS_IDS:
            initial_state = gtfs_routes.INITIAL_BUS_STATE[bus_id]
            
            self.buses[bus_id] = BusSimulatorGTFS(
                device_id=bus_id,
                route_info=initial_state,
                current_stop_sequence=initial_state["current_stop_sequence"],
                initial_battery_percent=initial_state["battery_percent"]
            )
            
            # Provisionar dispositivo
            model_id = "dtmi:nv2r8wn:dzaeymsn"
            self.clients[bus_id] = await self.provision_device(bus_id, model_id)
        
        # Inicializar estações
        for charger_id in CHARGER_IDS:
            self.chargers[charger_id] = ChargerSimulator(charger_id)
            
            # Provisionar dispositivo
            model_id = "dtmi:uo6xyxu9:m8hczfdfd"
            self.clients[charger_id] = await self.provision_device(charger_id, model_id)
        
        print("\n✓ Todos os dispositivos inicializados e conectados\n")
        
        # Mostrar estado inicial
        self._print_status_summary()
    
    def _print_status_summary(self):
        """Mostrar resumo do estado atual"""
        print("\n" + "="*80)
        print("ESTADO ATUAL DO SISTEMA")
        print("="*80)
        
        for bus_id in BUS_IDS:
            bus = self.buses[bus_id]
            progress = bus.get_route_progress()
            
            print(f"\n[{bus_id}] Rota {progress['route_id']} - {progress['route_name']}")
            print(f"  Paragem: {progress['current_stop']} /{progress['total_stops']} ({progress['current_stop_name']})")
            print(f"  Faltam: {progress['stops_remaining']} paragens")
            print(f"  Bateria: {bus.battery_percent:.1f}% ({bus.battery_kwh:.1f} kWh)")
            print(f"  Estado: {bus.state.value}")
            print(f"  Localização: ({bus.latitude:.6f}, {bus.longitude:.6f})")
        
        print("\n" + "="*80)
        print("ESTAÇÕES DE CARREGAMENTO")
        print("="*80)
        for charger_id in CHARGER_IDS:
            charger = self.chargers[charger_id]
            print(f"[{charger_id}] {charger.state} | Potência: {charger.current_power:.1f} kW")
        print("="*80 + "\n")
    
    def _execute_optimization(self):
        """Executar algoritmo de otimização"""
        current_datetime = datetime.now()
        
        # Executar otimização
        decisions = self.scheduler.optimize_charging_schedule(
            self.buses,
            self.chargers,
            current_datetime
        )
        
        # Mostrar resumo a cada minuto
        if self.simulation_time % 60 == 0:
            print(self.scheduler.get_optimization_summary())
        
        # Aplicar decisões
        for bus_id, decision in decisions.items():
            bus = self.buses[bus_id]
            action = decision["action"]
            
            if action == "START_CHARGING":
                charger_id = decision["charger"]
                charger = self.chargers[charger_id]
                
                if charger.connect_bus(bus_id):
                    bus.start_charging(charger_id, 150)
                    print(f"\n>>> {decision['reason']}")
            
            elif action == "STOP_CHARGING":
                if bus.connected_charger_id:
                    charger = self.chargers[bus.connected_charger_id]
                    charger.disconnect_bus()
                    bus.stop_charging()
                    print(f"\n>>> {decision['reason']}")
            
            elif action == "CONTINUE_CHARGING":
                if bus.connected_charger_id:
                    charger = self.chargers[bus.connected_charger_id]
                    charger.set_charging_power(150, bus.battery_percent)
            
            elif action == "WAIT":
                if self.simulation_time % 60 == 0:
                    print(f"[{bus_id}] ⏳ {decision['reason']}")
    
    async def send_telemetry(self, device_id, telemetry):
        """Enviar telemetria para IoT Central"""
        client = self.clients.get(device_id)
        if client:
            try:
                message = Message(json.dumps(telemetry))
                message.content_encoding = "utf-8"
                message.content_type = "application/json"
                await client.send_message(message)
            except Exception as e:
                print(f"[{device_id}] Erro ao enviar telemetria: {e}")
    
    async def update_loop(self):
        """Loop principal de atualização"""
        while True:
            try:
                self.simulation_time += UPDATE_INTERVAL_SECONDS
                
                # Executar otimização
                if self.simulation_time - self.last_optimization_time >= self.optimization_interval:
                    self._execute_optimization()
                    self.last_optimization_time = self.simulation_time
                
                # Atualizar autocarros
                for bus_id in BUS_IDS:
                    bus = self.buses[bus_id]
                    bus.update(UPDATE_INTERVAL_SECONDS)
                    
                    # Se parado na paragem, retomar após 20s
                    if bus.state.value == "IDLE_ON_ROUTE" and bus.time_in_state > 20:
                        if bus.current_stop_sequence < bus.route["total_stops"]:
                            bus.continue_route()
                    
                    # Se terminou rota e não está a carregar, voltar ao depósito
                    if (bus.current_stop_sequence >= bus.route["total_stops"] and 
                        bus.state.value == "IDLE_ON_ROUTE" and 
                        bus.time_in_state > 30):
                        bus.return_to_depot()
                    
                    # Atualizar potência de carregamento
                    if bus.state.value == "CHARGING" and bus.connected_charger_id:
                        charger = self.chargers[bus.connected_charger_id]
                        charger.set_charging_power(150, bus.battery_percent)
                
                # Atualizar estações
                for charger_id in CHARGER_IDS:
                    self.chargers[charger_id].update(UPDATE_INTERVAL_SECONDS)
                
                # Enviar telemetria
                for bus_id in BUS_IDS:
                    telemetry = self.buses[bus_id].get_telemetry()
                    await self.send_telemetry(bus_id, telemetry)
                    
                    # Log periódico
                    if self.simulation_time % 60 == 0:
                        progress = self.buses[bus_id].get_route_progress()
                        print(f"[{bus_id}] {telemetry['state']:15s} | "
                              f"Bateria: {telemetry['batteryLevel']:5.1f}% | "
                              f"Rota: {progress['current_stop']}/{progress['total_stops']} | "
                              f"GPS: ({telemetry['latitude']:.4f}, {telemetry['longitude']:.4f})")
                
                for charger_id in CHARGER_IDS:
                    telemetry = self.chargers[charger_id].get_telemetry()
                    await self.send_telemetry(charger_id, telemetry)
                    
                    if self.simulation_time % 60 == 0 and telemetry['currentPower'] > 0:
                        print(f"[{charger_id}] {telemetry['state']:10s} | "
                              f"Potência: {telemetry['currentPower']:6.1f} kW | "
                              f"Autocarro: {telemetry['connectedBus']}")
                
                await asyncio.sleep(UPDATE_INTERVAL_SECONDS)
                
            except Exception as e:
                print(f"✗ Erro no update loop: {e}")
                import traceback
                traceback.print_exc()
                await asyncio.sleep(5)
    
    async def run(self):
        """Executar simulação"""
        try:
            await self.initialize_devices()
            print("\n>>> INICIANDO SIMULAÇÃO COM ROTAS GTFS REAIS <<<")
            print(f">>> Otimização a cada {self.optimization_interval}s <<<")
            print(f">>> Telemetria a cada {TELEMETRY_INTERVAL_SECONDS}s <<<\n")
            
            await self.update_loop()
            
        except KeyboardInterrupt:
            print("\n\nSimulação interrompida pelo utilizador")
        except Exception as e:
            print(f"\n\nErro fatal: {e}")
            import traceback
            traceback.print_exc()
        finally:
            # Desconectar clientes
            for device_id, client in self.clients.items():
                if client:
                    await client.disconnect()
                    print(f"[{device_id}] Desconectado")

async def main():
    coordinator = GTFSSimulationCoordinator()
    await coordinator.run()

if __name__ == "__main__":
    asyncio.run(main())
