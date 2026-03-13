"""
Configuração de Rotas Reais STCP - Dados GTFS
Rotas 200, 201, 202 com paragens, horários e coordenadas GPS
"""

# Rota 200: Bolhão - Castelo do Queijo
ROUTE_200 = {
    "route_id": "200",
    "route_short_name": "200",
    "route_long_name": "Bolhão - Cast.queijo",
    "total_distance_km": 9.854,
    "total_stops": 30,
    "stops": [
        {"stop_sequence": 1, "stop_id": "BLRB1", "stop_name": "Bolhão", "latitude": 41.151868, "longitude": -8.607115, "distance_m": 0, "arrival_time": "06:00", "departure_time": "06:00"},
        {"stop_sequence": 2, "stop_id": "MCBL", "stop_name": "Mercado Do Bolhão", "latitude": 41.149509, "longitude": -8.607564, "distance_m": 326.09, "arrival_time": "06:01", "departure_time": "06:01"},
        {"stop_sequence": 3, "stop_id": "PRDJ", "stop_name": "Pr. D. João I", "latitude": 41.147581, "longitude": -8.609126, "distance_m": 621.59, "arrival_time": "06:02", "departure_time": "06:02"},
        {"stop_sequence": 4, "stop_id": "PRFL", "stop_name": "Pr.filipa De Lencastre", "latitude": 41.148261, "longitude": -8.612768, "distance_m": 944.8, "arrival_time": "06:03", "departure_time": "06:03"},
        {"stop_sequence": 5, "stop_id": "GGF", "stop_name": "Guil. G. Fernandes", "latitude": 41.147560, "longitude": -8.614767, "distance_m": 1174.83, "arrival_time": "06:04", "departure_time": "06:04"},
        {"stop_sequence": 6, "stop_id": "CMO", "stop_name": "Carmo", "latitude": 41.147223, "longitude": -8.616926, "distance_m": 1387.32, "arrival_time": "06:05", "departure_time": "06:05"},
        {"stop_sequence": 7, "stop_id": "HSA5", "stop_name": "Hosp. St. António", "latitude": 41.147766, "longitude": -8.622450, "distance_m": 1962.62, "arrival_time": "06:07", "departure_time": "06:07"},
        {"stop_sequence": 8, "stop_id": "PAL2", "stop_name": "Palácio", "latitude": 41.149145, "longitude": -8.625447, "distance_m": 2288.64, "arrival_time": "06:08", "departure_time": "06:08"},
        {"stop_sequence": 9, "stop_id": "PRG4", "stop_name": "Pr. Da Galiza", "latitude": 41.152531, "longitude": -8.627041, "distance_m": 2770.22, "arrival_time": "06:10", "departure_time": "06:10"},
        {"stop_sequence": 10, "stop_id": "JM1", "stop_name": "Junta Massarelos", "latitude": 41.152694, "longitude": -8.631221, "distance_m": 3129.94, "arrival_time": "06:10", "departure_time": "06:10"},
        {"stop_sequence": 11, "stop_id": "GGT1", "stop_name": "Gólgota", "latitude": 41.152639, "longitude": -8.633694, "distance_m": 3343.19, "arrival_time": "06:11", "departure_time": "06:11"},
        {"stop_sequence": 12, "stop_id": "PLNT1", "stop_name": "Planetário", "latitude": 41.153094, "longitude": -8.638289, "distance_m": 3746.09, "arrival_time": "06:12", "departure_time": "06:12"},
        {"stop_sequence": 13, "stop_id": "FCUP1", "stop_name": "Faculdade De Ciências", "latitude": 41.153838, "longitude": -8.641309, "distance_m": 4013.42, "arrival_time": "06:13", "departure_time": "06:13"},
        {"stop_sequence": 14, "stop_id": "JB1", "stop_name": "Jardim Botânico", "latitude": 41.154528, "longitude": -8.644222, "distance_m": 4271.82, "arrival_time": "06:13", "departure_time": "06:13"},
        {"stop_sequence": 15, "stop_id": "LRD1", "stop_name": "Lordelo", "latitude": 41.154389, "longitude": -8.649028, "distance_m": 4679.94, "arrival_time": "06:15", "departure_time": "06:15"},
        {"stop_sequence": 16, "stop_id": "PLM1", "stop_name": "Palmeiras", "latitude": 41.152356, "longitude": -8.652107, "distance_m": 5046.91, "arrival_time": "06:15", "departure_time": "06:15"},
        {"stop_sequence": 17, "stop_id": "FLUN1", "stop_name": "Fluvial (norte)", "latitude": 41.152139, "longitude": -8.655194, "distance_m": 5319.24, "arrival_time": "06:16", "departure_time": "06:16"},
        {"stop_sequence": 18, "stop_id": "PG1", "stop_name": "Paulo Da Gama", "latitude": 41.150856, "longitude": -8.658707, "distance_m": 5656.47, "arrival_time": "06:17", "departure_time": "06:17"},
        {"stop_sequence": 19, "stop_id": "PT3", "stop_name": "Pasteleira", "latitude": 41.150486, "longitude": -8.661488, "distance_m": 5895.45, "arrival_time": "06:17", "departure_time": "06:17"},
        {"stop_sequence": 20, "stop_id": "TRR3", "stop_name": "Torres", "latitude": 41.150749, "longitude": -8.664619, "distance_m": 6163.89, "arrival_time": "06:18", "departure_time": "06:18"},
        {"stop_sequence": 21, "stop_id": "PCL1", "stop_name": "Padre Luis Cabral", "latitude": 41.151806, "longitude": -8.668056, "distance_m": 6481.06, "arrival_time": "06:19", "departure_time": "06:19"},
        {"stop_sequence": 22, "stop_id": "UC1", "stop_name": "Univ. Católica", "latitude": 41.153538, "longitude": -8.670916, "distance_m": 6793.05, "arrival_time": "06:20", "departure_time": "06:20"},
        {"stop_sequence": 23, "stop_id": "MFZ1", "stop_name": "Mercado Da Foz", "latitude": 41.155048, "longitude": -8.673343, "distance_m": 7199.66, "arrival_time": "06:21", "departure_time": "06:21"},
        {"stop_sequence": 24, "stop_id": "LIEG1", "stop_name": "Pr. De Liége", "latitude": 41.155089, "longitude": -8.677168, "distance_m": 7692.57, "arrival_time": "06:22", "departure_time": "06:22"},
        {"stop_sequence": 25, "stop_id": "CRTO3", "stop_name": "Crasto", "latitude": 41.157713, "longitude": -8.679766, "distance_m": 8098.83, "arrival_time": "06:23", "departure_time": "06:23"},
        {"stop_sequence": 26, "stop_id": "MLH5", "stop_name": "Molhe", "latitude": 41.159880, "longitude": -8.681660, "distance_m": 8389.4, "arrival_time": "06:23", "departure_time": "06:23"},
        {"stop_sequence": 27, "stop_id": "FCH1", "stop_name": "Funchal", "latitude": 41.163190, "longitude": -8.683490, "distance_m": 8789.98, "arrival_time": "06:24", "departure_time": "06:24"},
        {"stop_sequence": 28, "stop_id": "HMLM3", "stop_name": "Homem Do Leme", "latitude": 41.163454, "longitude": -8.685965, "distance_m": 9077.4, "arrival_time": "06:25", "departure_time": "06:25"},
        {"stop_sequence": 29, "stop_id": "TIM1", "stop_name": "Timor", "latitude": 41.165587, "longitude": -8.687170, "distance_m": 9338.03, "arrival_time": "06:25", "departure_time": "06:25"},
        {"stop_sequence": 30, "stop_id": "CQ10", "stop_name": "Castelo Do Queijo", "latitude": 41.167422, "longitude": -8.689127, "distance_m": 9853.9, "arrival_time": "06:27", "departure_time": "06:27"},
    ]
}

# Rota 201: Aliados - Viso
ROUTE_201 = {
    "route_id": "201",
    "route_short_name": "201",
    "route_long_name": "Aliados-viso",
    "total_distance_km": 9.778,
    "total_stops": 26,
    "stops": [
        {"stop_sequence": 1, "stop_id": "AL1", "stop_name": "Av. Aliados", "latitude": 41.147208, "longitude": -8.610983, "distance_m": 0, "arrival_time": "07:38", "departure_time": "07:38"},
        {"stop_sequence": 2, "stop_id": "TRD6", "stop_name": "Trindade", "latitude": 41.151033, "longitude": -8.610854, "distance_m": 696.96, "arrival_time": "07:40", "departure_time": "07:40"},
        {"stop_sequence": 3, "stop_id": "PRFL", "stop_name": "Pr.filipa De Lencastre", "latitude": 41.148261, "longitude": -8.612768, "distance_m": 1194.03, "arrival_time": "07:41", "departure_time": "07:41"},
        {"stop_sequence": 4, "stop_id": "GGF", "stop_name": "Guil. G. Fernandes", "latitude": 41.147560, "longitude": -8.614767, "distance_m": 1423.58, "arrival_time": "07:42", "departure_time": "07:42"},
        {"stop_sequence": 5, "stop_id": "CMO", "stop_name": "Carmo", "latitude": 41.147223, "longitude": -8.616926, "distance_m": 1631.97, "arrival_time": "07:43", "departure_time": "07:43"},
        {"stop_sequence": 6, "stop_id": "HSA5", "stop_name": "Hosp. St. António", "latitude": 41.147766, "longitude": -8.622450, "distance_m": 2206.8, "arrival_time": "07:45", "departure_time": "07:45"},
        {"stop_sequence": 7, "stop_id": "PAL3", "stop_name": "Palácio", "latitude": 41.149512, "longitude": -8.625532, "distance_m": 2568.12, "arrival_time": "07:46", "departure_time": "07:46"},
        {"stop_sequence": 8, "stop_id": "PRG1", "stop_name": "Pr. Da Galiza", "latitude": 41.153444, "longitude": -8.626333, "distance_m": 3018.77, "arrival_time": "07:48", "departure_time": "07:48"},
        {"stop_sequence": 9, "stop_id": "BS1", "stop_name": "Boavista - B.sucesso", "latitude": 41.156403, "longitude": -8.627930, "distance_m": 3388.02, "arrival_time": "07:49", "departure_time": "07:49"},
        {"stop_sequence": 10, "stop_id": "BCM1", "stop_name": "Boavista-casa Da Música", "latitude": 41.158950, "longitude": -8.629420, "distance_m": 3787.25, "arrival_time": "07:52", "departure_time": "07:52"},
        {"stop_sequence": 11, "stop_id": "AGM1", "stop_name": "Agramonte", "latitude": 41.158948, "longitude": -8.634595, "distance_m": 4277.59, "arrival_time": "07:54", "departure_time": "07:54"},
        {"stop_sequence": 12, "stop_id": "ACRD1", "stop_name": "António Cardoso", "latitude": 41.159843, "longitude": -8.639918, "distance_m": 4735.65, "arrival_time": "07:56", "departure_time": "07:56"},
        {"stop_sequence": 13, "stop_id": "BSS1", "stop_name": "Bessa", "latitude": 41.160520, "longitude": -8.644060, "distance_m": 5091.66, "arrival_time": "07:58", "departure_time": "07:58"},
        {"stop_sequence": 14, "stop_id": "FOCO1", "stop_name": "Foco", "latitude": 41.161090, "longitude": -8.647460, "distance_m": 5384.38, "arrival_time": "07:59", "departure_time": "07:59"},
        {"stop_sequence": 15, "stop_id": "PINM1", "stop_name": "Pinheiro Manso", "latitude": 41.161845, "longitude": -8.651927, "distance_m": 5770.99, "arrival_time": "08:01", "departure_time": "08:01"},
        {"stop_sequence": 16, "stop_id": "SRV3", "stop_name": "Serralves", "latitude": 41.162848, "longitude": -8.657954, "distance_m": 6288.65, "arrival_time": "08:04", "departure_time": "08:04"},
        {"stop_sequence": 17, "stop_id": "PNV2", "stop_name": "Paulo Novais", "latitude": 41.163200, "longitude": -8.660057, "distance_m": 6470.52, "arrival_time": "08:05", "departure_time": "08:05"},
        {"stop_sequence": 18, "stop_id": "FTM1", "stop_name": "Fonte Da Moura", "latitude": 41.164505, "longitude": -8.662144, "distance_m": 6821.25, "arrival_time": "08:07", "departure_time": "08:07"},
        {"stop_sequence": 19, "stop_id": "BRV1", "stop_name": "Bairro Vilarinha", "latitude": 41.167065, "longitude": -8.659990, "distance_m": 7161.8, "arrival_time": "08:08", "departure_time": "08:08"},
        {"stop_sequence": 20, "stop_id": "LDD1", "stop_name": "Lidador", "latitude": 41.169798, "longitude": -8.657682, "distance_m": 7524.24, "arrival_time": "08:09", "departure_time": "08:09"},
        {"stop_sequence": 21, "stop_id": "PRO1", "stop_name": "Pereiró", "latitude": 41.172368, "longitude": -8.655497, "distance_m": 7865.77, "arrival_time": "08:10", "departure_time": "08:10"},
        {"stop_sequence": 22, "stop_id": "EZC1", "stop_name": "Ezequiel Campos", "latitude": 41.174449, "longitude": -8.653793, "distance_m": 8140.75, "arrival_time": "08:11", "departure_time": "08:11"},
        {"stop_sequence": 23, "stop_id": "MPAZ5", "stop_name": "Man.p.azevedo 3", "latitude": 41.176989, "longitude": -8.651836, "distance_m": 8522.05, "arrival_time": "08:13", "departure_time": "08:13"},
        {"stop_sequence": 24, "stop_id": "IMTT1", "stop_name": "Imtt", "latitude": 41.178485, "longitude": -8.648801, "distance_m": 8960.39, "arrival_time": "08:14", "departure_time": "08:14"},
        {"stop_sequence": 25, "stop_id": "VIS5", "stop_name": "Viso (metro)", "latitude": 41.177361, "longitude": -8.646500, "distance_m": 9306.3, "arrival_time": "08:16", "departure_time": "08:16"},
        {"stop_sequence": 26, "stop_id": "VIS3", "stop_name": "Viso", "latitude": 41.177840, "longitude": -8.642280, "distance_m": 9777.63, "arrival_time": "08:18", "departure_time": "08:18"},
    ]
}

# Rota 202: Aliados - Passeio Alegre
ROUTE_202 = {
    "route_id": "202",
    "route_short_name": "202",
    "route_long_name": "Aliados-passeio Alegre (via Av. Bessa)",
    "total_distance_km": 5.313,
    "total_stops": 16,
    "stops": [
        {"stop_sequence": 1, "stop_id": "SJB1", "stop_name": "S. João De Brito", "latitude": 41.166494, "longitude": -8.650585, "distance_m": 0, "arrival_time": "06:43", "departure_time": "06:43"},
        {"stop_sequence": 2, "stop_id": "ABM1", "stop_name": "Alberto Macedo", "latitude": 41.167151, "longitude": -8.654485, "distance_m": 336.7, "arrival_time": "06:44", "departure_time": "06:44"},
        {"stop_sequence": 3, "stop_id": "BRP1", "stop_name": "Bairro Da Previdência", "latitude": 41.165783, "longitude": -8.657654, "distance_m": 695.22, "arrival_time": "06:45", "departure_time": "06:45"},
        {"stop_sequence": 4, "stop_id": "BRV3", "stop_name": "Bairro Da Vilarinha", "latitude": 41.166094, "longitude": -8.659405, "distance_m": 925.14, "arrival_time": "06:45", "departure_time": "06:45"},
        {"stop_sequence": 5, "stop_id": "FTM2", "stop_name": "Fonte Da Moura", "latitude": 41.164191, "longitude": -8.662646, "distance_m": 1354.35, "arrival_time": "06:47", "departure_time": "06:47"},
        {"stop_sequence": 6, "stop_id": "ABVT1", "stop_name": "Av.da Boavista", "latitude": 41.162823, "longitude": -8.663403, "distance_m": 1525.1, "arrival_time": "06:47", "departure_time": "06:47"},
        {"stop_sequence": 7, "stop_id": "LGO4", "stop_name": "Liceu Garcia Orta", "latitude": 41.161528, "longitude": -8.666778, "distance_m": 1877.3, "arrival_time": "06:48", "departure_time": "06:48"},
        {"stop_sequence": 8, "stop_id": "RCRT2", "stop_name": "R.crasto", "latitude": 41.162000, "longitude": -8.671694, "distance_m": 2350.57, "arrival_time": "06:49", "departure_time": "06:49"},
        {"stop_sequence": 9, "stop_id": "LNEV2", "stop_name": "Lgo.nevogilde", "latitude": 41.162833, "longitude": -8.676306, "distance_m": 2757.63, "arrival_time": "06:50", "departure_time": "06:50"},
        {"stop_sequence": 10, "stop_id": "NEVG", "stop_name": "Nevogilde", "latitude": 41.161511, "longitude": -8.679230, "distance_m": 3082.04, "arrival_time": "06:51", "departure_time": "06:51"},
        {"stop_sequence": 11, "stop_id": "MLH3", "stop_name": "Molhe", "latitude": 41.160158, "longitude": -8.683185, "distance_m": 3483.16, "arrival_time": "06:52", "departure_time": "06:52"},
        {"stop_sequence": 12, "stop_id": "JNN2", "stop_name": "Jacinto Nunes", "latitude": 41.158107, "longitude": -8.681560, "distance_m": 3750.03, "arrival_time": "06:53", "departure_time": "06:53"},
        {"stop_sequence": 13, "stop_id": "CRTO4", "stop_name": "Crasto", "latitude": 41.156600, "longitude": -8.680260, "distance_m": 3936.85, "arrival_time": "06:53", "departure_time": "06:53"},
        {"stop_sequence": 14, "stop_id": "PING3", "stop_name": "Praia Dos Ingleses", "latitude": 41.152767, "longitude": -8.678563, "distance_m": 4490.81, "arrival_time": "06:54", "departure_time": "06:54"},
        {"stop_sequence": 15, "stop_id": "PORI2", "stop_name": "Praia Do Ourigo", "latitude": 41.149376, "longitude": -8.675942, "distance_m": 4937.66, "arrival_time": "06:56", "departure_time": "06:56"},
        {"stop_sequence": 16, "stop_id": "PASS1", "stop_name": "Passeio Alegre", "latitude": 41.148820, "longitude": -8.672750, "distance_m": 5313.2, "arrival_time": "06:57", "departure_time": "06:57"},
    ]
}

# Localização da Estação de Carregamento (Depósito STCP)
DEPOT_LOCATION = {
    "latitude": 41.183580,
    "longitude": -8.618978,
    "name": "Depósito STCP"
}

# Localizações das Estações de Carregamento (todas no mesmo depósito)
CHARGER_LOCATIONS = {
    "CS-001": {"latitude": 41.183580, "longitude": -8.618978},
    "CS-002": {"latitude": 41.183580, "longitude": -8.618978},
    "CS-003": {"latitude": 41.183580, "longitude": -8.618978}
}

# Estado Inicial dos Autocarros (baseado na configuração fornecida)
INITIAL_BUS_STATE = {
    "BUS-001": {
        "route": ROUTE_200,
        "current_stop_sequence": 25,  # Paragem 25 (CRTO3 - Crasto)
        "battery_percent": 30.0,
        "battery_kwh": 105.0,
        "state_description": "Ainda faltam 5 paragens"
    },
    "BUS-002": {
        "route": ROUTE_201,
        "current_stop_sequence": 2,  # Paragem 2 (TRD6 - Trindade)
        "battery_percent": 70.0,
        "battery_kwh": 245.0,
        "state_description": "Na segunda paragem"
    },
    "BUS-003": {
        "route": ROUTE_202,
        "current_stop_sequence": 16,  # Paragem 16 (PASS1 - última paragem)
        "battery_percent": 25.0,
        "battery_kwh": 87.5,
        "state_description": "A terminar a rota"
    }
}

def get_current_stop_info(route, stop_sequence):
    """Obter informação da paragem atual"""
    for stop in route["stops"]:
        if stop["stop_sequence"] == stop_sequence:
            return stop
    return None

def get_remaining_distance(route, current_stop_sequence):
    """Calcular distância restante até ao fim da rota"""
    total_distance = route["total_distance_km"] * 1000  # converter para metros
    
    current_stop = get_current_stop_info(route, current_stop_sequence)
    if not current_stop:
        return 0
    
    remaining_distance_m = total_distance - current_stop["distance_m"]
    return remaining_distance_m / 1000  # converter para km

def get_stops_remaining(route, current_stop_sequence):
    """Calcular número de paragens restantes"""
    return route["total_stops"] - current_stop_sequence

# Configuração para o algoritmo de otimização
OPTIMIZATION_CONFIG = {
    "min_battery_buffer_percent": 10,
    "charging_urgency_threshold_minutes": 60,
    "max_charging_sessions_simultaneous": 3,
    "preferred_charge_time_before_departure_minutes": 120
}

# Prioridades das rotas GTFS
ROUTE_PRIORITIES = {
    "200": "Alta",      # Rota 200: Bolhão - Castelo Queijo
    "201": "Normal",    # Rota 201: Aliados - Viso
    "202": "Critica"    # Rota 202: Aliados - Passeio Alegre (mais curta)
}

PRIORITY_LEVELS = {
    "Critica": 4,
    "Alta": 3,
    "Normal": 2,
    "Baixa": 1
}

def get_route_for_bus(bus_id):
    """Obter informação da rota atribuída"""
    initial_state = INITIAL_BUS_STATE.get(bus_id)
    if initial_state:
        route = initial_state["route"]
        return {
            "route_id": route["route_id"],
            "description": route["route_long_name"],
            "priority": ROUTE_PRIORITIES.get(route["route_id"], "Normal"),
            "departure_time": route["stops"][0]["departure_time"],
            "required_battery_percent": 20.0,  # Percentagem mínima necessária
            "distance_km": route["total_distance_km"]
        }
    return None

def get_priority_level(priority_name):
    """Converter nome de prioridade em nível numérico"""
    return PRIORITY_LEVELS.get(priority_name, 0)

def calculate_time_to_departure(current_time, departure_time_str):
    """Calcular minutos até hora de partida"""
    from datetime import datetime, timedelta
    hour, minute = map(int, departure_time_str.split(":"))
    departure = current_time.replace(hour=hour, minute=minute, second=0, microsecond=0)
    if departure < current_time:
        departure += timedelta(days=1)
    delta = departure - current_time
    return delta.total_seconds() / 60

def is_battery_sufficient_for_route(battery_percent, route_info):
    """Verificar se bateria é suficiente"""
    required_percent = route_info["required_battery_percent"]
    buffer = OPTIMIZATION_CONFIG["min_battery_buffer_percent"]
    return battery_percent >= (required_percent + buffer)
