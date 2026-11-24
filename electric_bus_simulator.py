import asyncio
import json
import math
import random
from datetime import datetime
from azure.iot.device.aio import IoTHubDeviceClient, ProvisioningDeviceClient
from azure.iot.device import Message

# ---------------------------------------------------------------------------
# Paragens reais das linhas 200/201/202 (nome, distancia acumulada em metros,
# latitude, longitude). Distancia aproximada por Haversine plana entre
# paragens consecutivas (mesma formula usada nas queries Gold/Notebooks).
# [CORRIGIDO por Claude] Substitui o modelo anterior de 9/7/6 paragens
# inventadas, que nao correspondiam a nenhuma paragem real da STCP.
# Fonte: API publica stcp.pt/api/route/<linha>/stops/direction (consultada em
# 2026-10-15). Linha 200: 30 paragens reais; Linha 201: 26; Linha 202: 30.
# ---------------------------------------------------------------------------
ROUTE_STOPS = {
    "Route-200": [  # Linha 200 — Bolhão → Castelo do Queijo
        {"name": 'Bolhão'                    , "distance":      0.0, "lat": 41.151966, "lon": -8.607095},
        {"name": 'Mercado do Bolhão'         , "distance":    275.5, "lat": 41.149509, "lon": -8.607564},
        {"name": 'Pr. D. João I'             , "distance":    526.4, "lat": 41.147578, "lon": -8.609125},
        {"name": 'Pr. Filipa Lencastre'      , "distance":    843.4, "lat": 41.148299, "lon": -8.612795},
        {"name": 'Guil. G. Fernandes'        , "distance":   1027.6, "lat": 41.147560, "lon": -8.614767},
        {"name": 'Carmo'                     , "distance":   1210.6, "lat": 41.147221, "lon": -8.616910},
        {"name": 'Hosp. St. António'         , "distance":   1677.6, "lat": 41.147766, "lon": -8.622450},
        {"name": 'Palácio'                   , "distance":   1971.2, "lat": 41.149145, "lon": -8.625447},
        {"name": 'Pr. da Galiza'             , "distance":   2369.9, "lat": 41.152531, "lon": -8.627041},
        {"name": 'Junta Massarelos'          , "distance":   2719.8, "lat": 41.152694, "lon": -8.631221},
        {"name": 'Gólgota'                   , "distance":   2926.5, "lat": 41.152639, "lon": -8.633694},
        {"name": 'Planetário'                , "distance":   3313.9, "lat": 41.153094, "lon": -8.638289},
        {"name": 'Faculdade de Ciências'     , "distance":   3579.5, "lat": 41.153838, "lon": -8.641309},
        {"name": 'Jardim Botânico'           , "distance":   3834.7, "lat": 41.154528, "lon": -8.644222},
        {"name": 'Lordelo'                   , "distance":   4236.6, "lat": 41.154389, "lon": -8.649028},
        {"name": 'Palmeiras'                 , "distance":   4578.9, "lat": 41.152356, "lon": -8.652107},
        {"name": 'Fluvial (Norte)'           , "distance":   4838.0, "lat": 41.152139, "lon": -8.655194},
        {"name": 'Paulo da Gama'             , "distance":   5164.4, "lat": 41.150856, "lon": -8.658707},
        {"name": 'Pasteleira'                , "distance":   5400.4, "lat": 41.150486, "lon": -8.661488},
        {"name": 'Torres'                    , "distance":   5663.7, "lat": 41.150749, "lon": -8.664619},
        {"name": 'Padre Luis Cabral'         , "distance":   5974.0, "lat": 41.151806, "lon": -8.668056},
        {"name": 'Univ. Católica'            , "distance":   6280.8, "lat": 41.153538, "lon": -8.670916},
        {"name": 'Mercado da Foz'            , "distance":   6543.9, "lat": 41.155048, "lon": -8.673343},
        {"name": 'Pr. de Liége'              , "distance":   6863.6, "lat": 41.155089, "lon": -8.677168},
        {"name": 'Crasto'                    , "distance":   7226.9, "lat": 41.157713, "lon": -8.679766},
        {"name": 'Molhe'                     , "distance":   7514.9, "lat": 41.159880, "lon": -8.681660},
        {"name": 'Funchal'                   , "distance":   7912.8, "lat": 41.163190, "lon": -8.683490},
        {"name": 'Homem do Leme'             , "distance":   8121.7, "lat": 41.163454, "lon": -8.685965},
        {"name": 'Timor'                     , "distance":   8379.0, "lat": 41.165587, "lon": -8.687170},
        {"name": 'Castelo do Queijo'         , "distance":   8640.2, "lat": 41.167422, "lon": -8.689127},
    ],
    "Route-201": [  # Linha 201 — Aliados → Viso
        {"name": 'Av. Aliados'               , "distance":      0.0, "lat": 41.147208, "lon": -8.610983},
        {"name": 'Trindade'                  , "distance":    424.7, "lat": 41.151033, "lon": -8.610854},
        {"name": 'Pr. Filipa Lencastre'      , "distance":    768.8, "lat": 41.148299, "lon": -8.612795},
        {"name": 'Guil. G. Fernandes'        , "distance":    952.9, "lat": 41.147560, "lon": -8.614767},
        {"name": 'Carmo'                     , "distance":   1136.0, "lat": 41.147221, "lon": -8.616910},
        {"name": 'Hosp. St. António'         , "distance":   1602.9, "lat": 41.147766, "lon": -8.622450},
        {"name": 'Palácio'                   , "distance":   1925.3, "lat": 41.149512, "lon": -8.625532},
        {"name": 'Pr. da Galiza'             , "distance":   2366.9, "lat": 41.153444, "lon": -8.626333},
        {"name": 'Boavista - B.Sucesso'      , "distance":   2721.4, "lat": 41.156403, "lon": -8.627930},
        {"name": 'Boavista-Casa da Música'   , "distance":   3030.3, "lat": 41.158950, "lon": -8.629420},
        {"name": 'Agramonte'                 , "distance":   3462.8, "lat": 41.158948, "lon": -8.634595},
        {"name": 'António Cardoso'           , "distance":   3918.6, "lat": 41.159843, "lon": -8.639918},
        {"name": 'Bessa'                     , "distance":   4272.8, "lat": 41.160520, "lon": -8.644060},
        {"name": 'Foco'                      , "distance":   4563.9, "lat": 41.161090, "lon": -8.647460},
        {"name": 'Pinheiro Manso'            , "distance":   4946.5, "lat": 41.161845, "lon": -8.651927},
        {"name": 'Serralves'                 , "distance":   5462.3, "lat": 41.162848, "lon": -8.657954},
        {"name": 'Paulo Novais'              , "distance":   5642.3, "lat": 41.163200, "lon": -8.660057},
        {"name": 'Fonte da Moura'            , "distance":   5869.1, "lat": 41.164505, "lon": -8.662144},
        {"name": 'Bairro Vilarinha'          , "distance":   6205.4, "lat": 41.167065, "lon": -8.659990},
        {"name": 'Lidador'                   , "distance":   6564.9, "lat": 41.169798, "lon": -8.657682},
        {"name": 'Pereiró'                   , "distance":   6903.6, "lat": 41.172368, "lon": -8.655497},
        {"name": 'Ezequiel Campos'           , "distance":   7174.9, "lat": 41.174449, "lon": -8.653793},
        {"name": 'Man.P.Azevedo 3'           , "distance":   7500.9, "lat": 41.176989, "lon": -8.651836},
        {"name": 'IMTT'                      , "distance":   7804.0, "lat": 41.178485, "lon": -8.648801},
        {"name": 'Viso (Metro)'              , "distance":   8033.1, "lat": 41.177361, "lon": -8.646500},
        {"name": 'Viso'                      , "distance":   8389.7, "lat": 41.177840, "lon": -8.642280},
    ],
    "Route-202": [  # Linha 202 — Aliados → Passeio Alegre (via Av. Bessa)
        {"name": 'Av.Aliados'                , "distance":      0.0, "lat": 41.148528, "lon": -8.610667},
        {"name": 'Trindade'                  , "distance":    362.9, "lat": 41.151695, "lon": -8.609587},
        {"name": 'Gonçalo Cristóvão'         , "distance":    640.3, "lat": 41.154194, "lon": -8.609611},
        {"name": 'Pr. da República'          , "distance":    834.0, "lat": 41.154023, "lon": -8.611917},
        {"name": 'Figueiroa'                 , "distance":   1299.2, "lat": 41.155956, "lon": -8.616856},
        {"name": 'Carvalhosa'                , "distance":   1582.6, "lat": 41.156512, "lon": -8.620165},
        {"name": 'Hospital Militar'          , "distance":   1929.2, "lat": 41.157176, "lon": -8.624218},
        {"name": 'Boavista Brasília'         , "distance":   2139.3, "lat": 41.157587, "lon": -8.626672},
        {"name": 'Boavista-Casa da Música'   , "distance":   2403.1, "lat": 41.159458, "lon": -8.628619},
        {"name": 'Graciosa'                  , "distance":   2798.7, "lat": 41.162921, "lon": -8.627502},
        {"name": 'Casa de Saúde da Boavista' , "distance":   3225.4, "lat": 41.164532, "lon": -8.632138},
        {"name": 'Sidónio Pais'              , "distance":   3632.0, "lat": 41.164563, "lon": -8.637004},
        {"name": 'Av. do Bessa'              , "distance":   4147.6, "lat": 41.165323, "lon": -8.643091},
        {"name": 'S.João Bosco'              , "distance":   4554.6, "lat": 41.166131, "lon": -8.647841},
        {"name": 'S. João de Brito'          , "distance":   4787.4, "lat": 41.166494, "lon": -8.650585},
        {"name": 'Alberto Macedo'            , "distance":   5121.3, "lat": 41.167151, "lon": -8.654485},
        {"name": 'Bairro da Previdência'     , "distance":   5426.6, "lat": 41.165783, "lon": -8.657654},
        {"name": 'Bairro da Vilarinha'       , "distance":   5576.9, "lat": 41.166094, "lon": -8.659405},
        {"name": 'Fonte da Moura'            , "distance":   5920.4, "lat": 41.164191, "lon": -8.662646},
        {"name": 'Av. da Boavista'           , "distance":   6084.9, "lat": 41.162823, "lon": -8.663403},
        {"name": 'Liceu Garcia Orta'         , "distance":   6401.4, "lat": 41.161528, "lon": -8.666778},
        {"name": 'R.Crasto'                  , "distance":   6815.6, "lat": 41.162000, "lon": -8.671694},
        {"name": 'Lgo.Nevogilde'             , "distance":   7211.9, "lat": 41.162833, "lon": -8.676306},
        {"name": 'Nevogilde'                 , "distance":   7496.9, "lat": 41.161511, "lon": -8.679230},
        {"name": 'Molhe'                     , "distance":   7859.9, "lat": 41.160158, "lon": -8.683185},
        {"name": 'Jacinto Nunes'             , "distance":   8125.0, "lat": 41.158107, "lon": -8.681560},
        {"name": 'Crasto'                    , "distance":   8324.5, "lat": 41.156600, "lon": -8.680260},
        {"name": 'Praia dos Ingleses'        , "distance":   8773.0, "lat": 41.152767, "lon": -8.678563},
        {"name": 'Praia do Ourigo'           , "distance":   9208.5, "lat": 41.149376, "lon": -8.675942},
        {"name": 'Passeio Alegre'            , "distance":   9482.3, "lat": 41.148820, "lon": -8.672750},
    ],
}


def _approx_distance_m(lat1, lon1, lat2, lon2):
    """Aproximação plana da fórmula de Haversine (mesma usada nas queries Gold/Notebooks)."""
    dlat = lat1 - lat2
    dlon = (lon1 - lon2) * math.cos(math.radians(lat1))
    return 111000.0 * math.sqrt(dlat ** 2 + dlon ** 2)

# Distâncias de cada terminal até à Central de Carregamento (metros)
# Estação de Recolha de Via Norte, Bonjóia, Campanhã, Porto
TERMINAL_TO_CHARGING = {
    "Castelo do Queijo": 12000,
    "Viso (Terminal)":   8000,
    "Passeio Alegre":    11000,
    "Bolhão":            3000,
    "Aliados":           4000,
}

# Tempo que o autocarro fica parado no terminal antes de inverter (em ciclos de 5s)
TERMINAL_DWELL_CYCLES = 4  # 4 x 5s = 20s

# [CORRIGIDO por Claude] Factor de aceleração do carregamento para fins de demonstração,
# no mesmo espírito do sim_speed acelerado da condução (~36x a velocidade real do autocarro).
# Sem isto, carregar de 20% a 80% (210 kWh a 120 kW) demoraria ~2h de tempo real.
CHARGE_ACCELERATION = 30.0


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

        self._base_stops = ROUTE_STOPS.get(route, [])
        self.stops = list(self._base_stops)
        self.trip_distance = 0.0          # contador interno acelerado (lógica de paragens)

        self.current_stop = self.stops[0]["name"] if self.stops else "Desconhecida"
        self.next_stop = self.stops[1]["name"] if len(self.stops) > 1 else "Central de Carregamento"

        self.direction = 1
        self.trip_count = 0
        self.at_terminal_cycles = 0
        self.waiting_at_terminal = False
        self.heading_to_charging = False

        # [CORRIGIDO por Claude] Ciclo de carregamento fechado — antes, ao atingir o SOC
        # mínimo, o autocarro simplesmente desligava-se (self.finished). Agora dirige-se
        # à Central de Carregamento, aguarda uma estação livre, carrega e regressa à rota.
        self.connected_station = None
        self.charge_trip_origin = None
        self.charge_trip_total_m = 0.0
        self.charge_trip_distance = 0.0
        self.SOC_CHARGE_TARGET = 80.0  # = SOC_IDEAL_MAX (ver Notebook 3/Regra 8)
        self.charge_cycles_completed = 0  # usado por main.py para saber quando parar

        bus_config = {
            "BUS-001": {
                "battery_level": 95.0,
                "status": "inTransit",
                "latitude": 41.151868,
                "longitude": -8.607115
            },
            "BUS-002": {
                "battery_level": 95.0,
                "status": "inTransit",
                "latitude": 41.147208,
                "longitude": -8.610983
            },
            "BUS-003": {
                "battery_level": 95.0,
                "status": "inTransit",
                "latitude": 41.157000,
                "longitude": -8.629000
            }
        }

        config = bus_config.get(device_id, {
            "battery_level": 95.0,
            "status": "inTransit",
            "latitude": station_location["latitude"],
            "longitude": station_location["longitude"]
        })

        self.depot_lat = station_location["latitude"]
        self.depot_lon = station_location["longitude"]

        self.operational_status = config["status"]
        self.battery_level = config["battery_level"]
        self.battery_kwh = (self.battery_level / 100) * self.battery_capacity
        self.latitude = config["latitude"]
        self.longitude = config["longitude"]
        self.instant_consumption = 0.0
        self.remaining_range = self.battery_kwh / self.avg_consumption
        self.battery_temperature = random.uniform(18, 25)
        self.connected_charger = None
        self.charging_power = 0.0

        self.SOC_MIN = 20.0
        self.start_time = None
        self.telemetry_count = 0

    def _get_terminal_name(self):
        return self.stops[-1]["name"] if self.stops else "Central de Carregamento"

    def _get_route_length(self):
        return self.stops[-1]["distance"] if self.stops else 0

    def _get_intermediate_stops(self):
        return self.stops[:-1] if len(self.stops) > 1 else self.stops

    def _reverse_route(self):
        # [CORRIGIDO por Claude] A versão anterior reutilizava as distâncias do
        # sentido de ida posicionalmente — incorreto, pois os intervalos entre
        # paragens não são simétricos. Agora recalcula a distância acumulada real
        # (Haversine) a partir das coordenadas das paragens na ordem invertida.
        reversed_stops = list(reversed(self._base_stops))
        new_stops = []
        cumulative = 0.0
        prev = None
        for s in reversed_stops:
            if prev is not None:
                cumulative += _approx_distance_m(prev["lat"], prev["lon"], s["lat"], s["lon"])
            new_stops.append({
                "name": s["name"],
                "distance": round(cumulative, 1),
                "lat": s["lat"],
                "lon": s["lon"],
            })
            prev = s

        self.stops = new_stops

    def _has_enough_battery_for_route(self):
        route_length_km = self._get_route_length() / 1000.0
        energy_needed = route_length_km * self.avg_consumption
        energy_available = ((self.battery_level - self.SOC_MIN) / 100.0) * self.battery_capacity
        return energy_available >= energy_needed

    def _interpolate_position(self):
        """
        [CORRIGIDO por Claude] Substitui o random walk anterior (GPS sem relação
        com a rota real). Interpola latitude/longitude ao longo da sequência real
        de paragens (self.stops) com base no trip_distance actual — aproximação
        linear entre as duas paragens que o delimitam.
        """
        if not self.stops:
            return

        if self.trip_distance <= self.stops[0]["distance"]:
            self.latitude = self.stops[0]["lat"]
            self.longitude = self.stops[0]["lon"]
            return

        for i in range(len(self.stops) - 1):
            a, b = self.stops[i], self.stops[i + 1]
            if a["distance"] <= self.trip_distance <= b["distance"]:
                span = b["distance"] - a["distance"]
                frac = (self.trip_distance - a["distance"]) / span if span > 0 else 0.0
                self.latitude = a["lat"] + (b["lat"] - a["lat"]) * frac
                self.longitude = a["lon"] + (b["lon"] - a["lon"]) * frac
                return

        self.latitude = self.stops[-1]["lat"]
        self.longitude = self.stops[-1]["lon"]

    def _start_heading_to_charging(self):
        """
        [CORRIGIDO por Claude] Inicia a deslocação real até à Central de Carregamento,
        a partir da posição actual (GPS interpolado, tal como nas paragens reais),
        em vez de simplesmente terminar a simulação.
        """
        self.heading_to_charging = True
        self.operational_status = "headingToCharging"
        self.waiting_at_terminal = False
        self.charge_trip_origin = (self.latitude, self.longitude)
        self.charge_trip_total_m = max(
            _approx_distance_m(self.latitude, self.longitude, self.depot_lat, self.depot_lon), 1.0
        )
        self.charge_trip_distance = 0.0
        self.next_stop = "Central de Carregamento"
        print(f"\n  !!! {self.device_id} sem autonomia para próxima rota "
              f"— a seguir para a Central de Carregamento "
              f"(bateria: {self.battery_level:.1f}%) !!!\n")

    def _advance_to_charging(self):
        sim_speed = 2000.0 * random.uniform(0.85, 1.15)
        self.charge_trip_distance += sim_speed
        frac = min(self.charge_trip_distance / self.charge_trip_total_m, 1.0)
        ox, oy = self.charge_trip_origin
        self.latitude = ox + (self.depot_lat - ox) * frac
        self.longitude = oy + (self.depot_lon - oy) * frac

        if frac >= 1.0:
            self.latitude = self.depot_lat
            self.longitude = self.depot_lon
            self.operational_status = "waitingForCharger"
            self.current_stop = "Central de Carregamento"
            print(f"\n  {self.device_id} chegou à Central de Carregamento — a aguardar estação livre.\n")

    async def _try_claim_station(self, charging_stations):
        for station in charging_stations.values():
            if station.status == "available":
                power = station.max_power
                await station.start_charging(self.device_id, power)
                await self.start_charging(station.device_id, power)
                self.connected_station = station
                print(f"\n  {self.device_id} começou a carregar em {station.device_id} ({power} kW)\n")
                return

    async def _finish_charging_and_resume(self):
        station = self.connected_station
        if station is not None:
            await station.stop_charging()
        await self.stop_charging()

        self.connected_station = None
        self.heading_to_charging = False
        self.stops = list(self._base_stops)
        self.direction = 1
        self.trip_distance = 0.0
        self.latitude = self.depot_lat
        self.longitude = self.depot_lon
        self.current_stop = "Central de Carregamento"
        self.next_stop = self.stops[0]["name"] if self.stops else "Central de Carregamento"
        self.operational_status = "inTransit"
        self.charge_cycles_completed += 1
        print(f"\n  {self.device_id} terminou o carregamento ({self.battery_level:.1f}%) "
              f"— regressa à rota {self.assigned_route} "
              f"[ciclo de carregamento #{self.charge_cycles_completed}]\n")

    def _update_stop_info(self):
        if not self.stops or self.waiting_at_terminal:
            return

        terminal_distance = self._get_route_length()
        terminal_name = self._get_terminal_name()

        # 1. Verificar PRIMEIRO se chegou ao terminal
        if self.trip_distance >= terminal_distance:
            self.trip_count += 1
            direction_label = "IDA" if self.direction == 1 else "REGRESSO"
            print(f"\n  *** {self.device_id} chegou a {terminal_name} "
                  f"[viagem #{self.trip_count} — {direction_label}] "
                  f"(bateria: {self.battery_level:.1f}%) ***")

            self.current_stop = terminal_name
            self.latitude = self.stops[-1]["lat"]
            self.longitude = self.stops[-1]["lon"]

            if self._has_enough_battery_for_route():
                self.next_stop = self.stops[0]["name"]
                self.operational_status = "parked"
                self.waiting_at_terminal = True
                self.at_terminal_cycles = 0
            else:
                # [CORRIGIDO por Claude] Em vez de ficar à espera indefinidamente
                # (self.finished), o autocarro segue mesmo para a Central de Carregamento.
                self._start_heading_to_charging()
            return

        # 2. Actualização normal — só paragens intermédias
        intermediate = self._get_intermediate_stops()

        current_name = self.current_stop
        new_current = intermediate[0]["name"]
        new_next = intermediate[1]["name"] if len(intermediate) > 1 else terminal_name

        for i, stop in enumerate(intermediate):
            if self.trip_distance >= stop["distance"]:
                new_current = stop["name"]
                if i + 1 < len(intermediate):
                    new_next = intermediate[i + 1]["name"]
                else:
                    new_next = terminal_name

        if new_current != current_name:
            print(f"  {self.device_id} >> {new_current}  (proxima: {new_next})")

        self.current_stop = new_current
        self.next_stop = new_next

    def _try_depart_from_terminal(self):
        """
        Chamado em cada ciclo quando o autocarro está parado num terminal da rota
        (com bateria suficiente). Inverte a rota após TERMINAL_DWELL_CYCLES.
        """
        self.at_terminal_cycles += 1
        if self.at_terminal_cycles >= TERMINAL_DWELL_CYCLES:
            self._reverse_route()
            self.direction *= -1
            self.trip_distance = 0.0
            self.waiting_at_terminal = False
            self.at_terminal_cycles = 0
            self.operational_status = "inTransit"

            new_origin = self.stops[0]["name"]
            new_destination = self.stops[-1]["name"]
            direction_label = "IDA" if self.direction == 1 else "REGRESSO"
            self.current_stop = new_origin
            self.next_stop = self.stops[1]["name"] if len(self.stops) > 1 else "Central de Carregamento"
            print(f"\n  {self.device_id} parte de {new_origin} — {direction_label}: "
                  f"{new_origin} → {new_destination} "
                  f"(bateria: {self.battery_level:.1f}%)\n")

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
            print(f"Connected: {self.device_id} ({self.operational_status})")
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
            "state": self.operational_status,
            "distanceTraveled": round(self.trip_distance, 2),
            "tripCount": self.trip_count,
            "currentStop": self.current_stop,
            "nextStop": self.next_stop
        }
        message = Message(json.dumps(telemetry))
        message.content_type = "application/json"
        message.content_encoding = "utf-8"
        try:
            await self.client.send_message(message)
            self.telemetry_count += 1
        except Exception as e:
            print(f"Error sending telemetry: {e}")

    def update_state(self):
        if self.operational_status == "charging":
            if self.battery_level < 95:
                # [CORRIGIDO por Claude] Faltava multiplicar por 5 (segundos por ciclo) —
                # a energia só considerava kWh/segundo, carregava a 1/5 do ritmo pretendido.
                # CHARGE_ACCELERATION acelera o carregamento para fins de demonstração,
                # tal como sim_speed já acelera a condução.
                energy_gain = (self.charging_power * 0.92 / 3600) * 5 * CHARGE_ACCELERATION
                self.battery_kwh = min(self.battery_capacity * 0.95, self.battery_kwh + energy_gain)
                self.battery_level = (self.battery_kwh / self.battery_capacity) * 100
                self.battery_temperature = min(40.0, self.battery_temperature + random.uniform(0.03, 0.08))
                self.instant_consumption = -self.charging_power
            else:
                self.instant_consumption = 0.0

        elif self.operational_status == "headingToCharging":
            self._advance_to_charging()
            self.battery_kwh = max(0, self.battery_kwh - 0.05)
            self.battery_level = (self.battery_kwh / self.battery_capacity) * 100
            self.instant_consumption = self.avg_consumption * 50
            self.battery_temperature = min(35.0, self.battery_temperature + random.uniform(0.02, 0.05))

        elif self.operational_status == "waitingForCharger":
            self.battery_kwh = max(0, self.battery_kwh - 0.0001)
            self.battery_level = (self.battery_kwh / self.battery_capacity) * 100
            self.instant_consumption = 0.0
            self.battery_temperature = max(20.0, self.battery_temperature - random.uniform(0.01, 0.03))

        elif self.operational_status == "inTransit":
            # --- Lógica interna acelerada (controla paragens e duração da simulação) ---
            # [CORRIGIDO por Claude] Velocidade e consumo eram fixos e iguais para todos os
            # autocarros — bateria ficava sempre idêntica entre autocarros. Agora variam por
            # ciclo (trânsito/condução na velocidade; desvios e paragens não planeadas no consumo).
            sim_speed = 2000.0 * random.uniform(0.85, 1.15)  # metros por ciclo (acelerado)
            self.trip_distance += sim_speed

            consumo_efetivo = self.avg_consumption * random.uniform(1.00, 1.25)
            energy_consumed = (sim_speed / 1000.0) * consumo_efetivo / 0.36
            self.battery_kwh = max(0, self.battery_kwh - energy_consumed)
            self.battery_level = (self.battery_kwh / self.battery_capacity) * 100
            self.instant_consumption = self.avg_consumption * 50
            self.battery_temperature = min(35.0, self.battery_temperature + random.uniform(0.02, 0.05))

            self._interpolate_position()
            self._update_stop_info()

        elif self.operational_status == "parked":
            self.battery_kwh = max(0, self.battery_kwh - 0.0001)
            self.battery_level = (self.battery_kwh / self.battery_capacity) * 100
            self.instant_consumption = 0.0
            self.battery_temperature = max(20.0, self.battery_temperature - random.uniform(0.01, 0.03))

            if self.waiting_at_terminal:
                self._try_depart_from_terminal()

        if self.avg_consumption > 0:
            self.remaining_range = self.battery_kwh / self.avg_consumption
        else:
            self.remaining_range = 0

    def needs_charging(self):
        return self.battery_level <= self.SOC_MIN

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

    async def simulate(self, stop_event, charging_stations):
        """
        [CORRIGIDO por Claude] Ciclo fechado: cada autocarro corre a sua rota
        indefinidamente, indo carregar à Central sempre que necessário e
        regressando depois à rota — já não termina quando atinge o SOC mínimo.
        A simulação só pára com Ctrl+C (stop_event activado externamente).
        """
        self.start_time = datetime.now()

        while not stop_event.is_set():
            try:
                self.update_state()

                # Segurança: se o SOC cair ao mínimo a meio de uma rota (não devia
                # acontecer em condições normais — cada rota consome só ~3-4% SOC),
                # desvia imediatamente para a Central em vez de continuar.
                if (self.operational_status == "inTransit"
                        and self.needs_charging()
                        and not self.heading_to_charging):
                    self._start_heading_to_charging()

                if self.operational_status == "waitingForCharger":
                    await self._try_claim_station(charging_stations)
                elif (self.operational_status == "charging"
                        and self.battery_level >= self.SOC_CHARGE_TARGET):
                    await self._finish_charging_and_resume()

                await self.send_telemetry()
                await asyncio.sleep(5)
            except Exception as e:
                print(f"Error in simulation ({self.device_id}): {e}")
                await asyncio.sleep(5)

        print(f"  {self.device_id} terminou a simulação.")

    async def disconnect(self):
        if self.client:
            await self.client.disconnect()
