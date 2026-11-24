import asyncio
from datetime import datetime
from charging_station_simulator import ChargingStationSimulator
from electric_bus_simulator import ElectricBusSimulator
import config

charging_stations = {}
buses = {}

# [CORRIGIDO por Claude] Condicao de paragem finita, a pedido: a simulacao corre ate
# cada autocarro completar pelo menos este numero de ciclos de carregamento completos
# (esgotar -> carregar -> regressar a rota). MAX_RUNTIME_MINUTES e uma rede de seguranca
# caso algo bloqueie o ciclo (ex. todas as estacoes indisponiveis).
TARGET_CHARGE_CYCLES = 1
MAX_RUNTIME_MINUTES = 30


def print_final_summary(start_time):
    """Imprime o resumo final da simulacao quando esta termina."""
    end_time = datetime.now()
    elapsed = end_time - start_time
    elapsed_minutes = int(elapsed.total_seconds() // 60)
    elapsed_seconds = int(elapsed.total_seconds() % 60)

    print("\n" + "=" * 60)
    print("  SIMULACAO TERMINADA — RESUMO FINAL")
    print("=" * 60)
    print(f"  Duracao total: {elapsed_minutes}m {elapsed_seconds}s")
    print(f"  Hora de inicio: {start_time.strftime('%H:%M:%S')}")
    print(f"  Hora de fim:    {end_time.strftime('%H:%M:%S')}")
    print("=" * 60)

    print("\n  ESTADO FINAL DOS AUTOCARROS")
    print("-" * 60)
    for bus_id, bus in buses.items():
        battery_pct = bus.battery_level
        battery_kwh = (battery_pct / 100.0) * bus.battery_capacity
        # [CORRIGIDO por Claude] bus.distance_traveled era um contador morto — nunca
        # enviado ao IoT Central, sem a variabilidade de velocidade/consumo. A distância
        # real que gera o GPS e a telemetria enviada e trip_distance.
        distance_km = bus.trip_distance / 1000.0

        # Determinar alerta
        if battery_pct <= bus.SOC_MIN:
            alerta = "CARREGAR AGORA"
        elif battery_pct <= 30.0:
            alerta = "CARREGAR EM BREVE"
        else:
            alerta = "OK"

        print(f"  {bus.device_id}")
        print(f"    Rota:             {bus.assigned_route}")
        print(f"    Bateria:          {battery_pct:.1f}% ({battery_kwh:.1f} kWh)")
        print(f"    Distancia:        {distance_km:.2f} km")
        print(f"    Telemetrias:      {bus.telemetry_count}")
        print(f"    Estado operac.:   {bus.operational_status}")
        print(f"    Alerta bateria:   {alerta}")
        print()

    print("  ESTADO FINAL DAS ESTACOES DE CARREGAMENTO")
    print("-" * 60)
    for cs_id, station in charging_stations.items():
        print(f"  {station.device_id}")
        print(f"    Estado:           {station.status}")
        print(f"    Energia entregue: {station.energy_delivered:.2f} kWh")
        print(f"    Temperatura:      {station.charger_temperature:.1f} C")
        print(f"    Telemetrias:      {station.telemetry_count}")
        print()

    print("=" * 60)
    print("  Todos os dispositivos desligados do Azure IoT Central.")
    print("=" * 60 + "\n")


async def watch_and_stop_when_done(bus_list, stop_event, start_time):
    """
    [CORRIGIDO por Claude] Para a simulacao automaticamente quando todos os autocarros
    tiverem completado TARGET_CHARGE_CYCLES ciclos de carregamento, ou ao fim de
    MAX_RUNTIME_MINUTES (rede de seguranca), o que ocorrer primeiro.
    """
    while True:
        elapsed_minutes = (datetime.now() - start_time).total_seconds() / 60.0

        if all(b.charge_cycles_completed >= TARGET_CHARGE_CYCLES for b in bus_list):
            print(f"\n  Todos os autocarros completaram {TARGET_CHARGE_CYCLES} "
                  f"ciclo(s) de carregamento — a parar...")
            stop_event.set()
            return

        if elapsed_minutes >= MAX_RUNTIME_MINUTES:
            print(f"\n  Limite de tempo ({MAX_RUNTIME_MINUTES} min) atingido — a parar...")
            stop_event.set()
            return

        await asyncio.sleep(5)


async def run_all_simulators():

    print("=" * 60)
    print("  STCP — Simulacao de Frota de Autocarros Electricos")
    print("=" * 60)
    print(f"  Autocarros:          {len(config.ELECTRIC_BUSES)}")
    print(f"  Estacoes de carga:   {len(config.CHARGING_STATIONS)}")
    # [CORRIGIDO por Claude] Os autocarros ja nao terminam ao atingir o SOC minimo —
    # vao carregar a Central e regressam a rota. A simulacao para automaticamente
    # quando todos completarem TARGET_CHARGE_CYCLES ciclos (ou ao fim do tempo limite).
    print(f"  Condicao de paragem: {TARGET_CHARGE_CYCLES} ciclo(s) de carregamento "
          f"por autocarro (max. {MAX_RUNTIME_MINUTES} min)")
    print("=" * 60)

    # Evento partilhado — activado pelo vigilante (ou por Ctrl+C) para parar tudo.
    stop_event = asyncio.Event()
    start_time = datetime.now()

    tasks = []

    # --- Estacoes de carregamento ---
    for station_id, station_config in config.CHARGING_STATIONS.items():
        station = ChargingStationSimulator(
            device_id=station_config["device_id"],
            id_scope=config.ID_SCOPE,
            primary_key=station_config["primary_key"]
        )
        charging_stations[station_id] = station

        async def run_station(s):
            await s.connect()
            await s.simulate(stop_event)

        tasks.append(asyncio.create_task(run_station(station)))

    # --- Autocarros electricos ---
    bus_list = []
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
        bus_list.append(bus)

        async def run_bus(b):
            await b.connect()
            await b.simulate(stop_event, charging_stations)

        tasks.append(asyncio.create_task(run_bus(bus)))

    # --- Vigilante: para a simulacao quando a condicao de paragem for atingida ---
    tasks.append(asyncio.create_task(watch_and_stop_when_done(bus_list, stop_event, start_time)))

    print(f"\n  Todos os simuladores iniciados.")
    print(f"  Telemetria a cada {config.TELEMETRY_INTERVAL} segundo(s).")
    print("  Prima Ctrl+C para parar manualmente.\n")

    try:
        # Aguarda que todas as tarefas terminem
        await asyncio.gather(*tasks, return_exceptions=True)
    except KeyboardInterrupt:
        print("\n\n  Interrupcao manual — a parar...")
        stop_event.set()

    # Resumo final
    print_final_summary(start_time)

    # Desligar todos os dispositivos
    for station in charging_stations.values():
        try:
            await station.disconnect()
        except Exception:
            pass
    for bus in buses.values():
        try:
            await bus.disconnect()
        except Exception:
            pass


def main():
    if config.ID_SCOPE == "your-id-scope-here":
        print("=" * 60)
        print("  ERRO: Configure as credenciais do Azure IoT Central")
        print("  Edite o ficheiro .env com o ID_SCOPE e as chaves.")
        print("=" * 60)
        return

    try:
        asyncio.run(run_all_simulators())
    except KeyboardInterrupt:
        print("\n  Simulacao interrompida pelo utilizador.")


if __name__ == "__main__":
    main()