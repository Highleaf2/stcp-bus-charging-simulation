"""
Simulador de Autocarro com Rotas GTFS Reais
Baseado em dados reais do STCP Porto
"""

import random
import time
from enum import Enum
import math
from datetime import datetime, timedelta

class BusState(Enum):
    """Estados possíveis do autocarro"""
    PARKED = "PARKED"              # Estacionado no depósito
    IDLE_DEPOT = "IDLE_DEPOT"      # No depósito, sistemas ligados
    CHARGING = "CHARGING"           # A carregar
    ROUTE = "ROUTE"                 # Em rota (a andar)
    IDLE_ON_ROUTE = "IDLE_ON_ROUTE" # Parado na rota (paragem, sinal)
    RETURNING = "RETURNING"         # A regressar ao depósito

class BusSimulatorGTFS:
    """
    Simulador de autocarro que segue rotas GTFS reais
    """
    
    def __init__(self, device_id, route_info, current_stop_sequence, initial_battery_percent):
        self.device_id = device_id
        
        # Configuração da rota
        self.route = route_info["route"]
        self.current_stop_sequence = current_stop_sequence
        self.current_stop = self._get_stop_by_sequence(current_stop_sequence)
        
        # Bateria
        self.BATTERY_CAPACITY_KWH = 350.0
        self.battery_percent = initial_battery_percent
        self.battery_kwh = route_info["battery_kwh"]
        self.battery_temperature = random.uniform(18, 22)
        
        # Posição GPS (começa na paragem atual)
        if self.current_stop:
            self.latitude = self.current_stop["latitude"]
            self.longitude = self.current_stop["longitude"]
        else:
            self.latitude = 41.183580  # Depósito
            self.longitude = -8.618978
        
        # Estado
        self.state = BusState.ROUTE if current_stop_sequence < route_info["route"]["total_stops"] else BusState.IDLE_DEPOT
        self.state_description = route_info["state_description"]
        
        # Consumo
        self.CONSUMPTION_PARKED = 0.0
        self.CONSUMPTION_IDLE = random.uniform(2, 3)
        self.CONSUMPTION_ROUTE_KWH_PER_KM = 1.5  # kWh por km
        self.SELF_DISCHARGE_RATE = 0.3 / 3600
        
        # Carregamento
        self.connected_charger_id = None
        self.charging_power_kw = 0
        
        # Tracking
        self.time_in_state = 0
        self.distance_to_next_stop_km = 0
        self.speed_kmh = 0
        
        # Calcular distância até próxima paragem
        if self.state == BusState.ROUTE:
            self._calculate_distance_to_next_stop()
        
        print(f"[{device_id}] Inicializado - Rota: {self.route['route_short_name']} | "
              f"Paragem: {current_stop_sequence}/{self.route['total_stops']} | "
              f"Bateria: {self.battery_percent:.1f}% ({self.battery_kwh:.1f} kWh) | "
              f"Estado: {self.state_description}")
    
    def _get_stop_by_sequence(self, sequence):
        """Obter paragem pela sequência"""
        for stop in self.route["stops"]:
            if stop["stop_sequence"] == sequence:
                return stop
        return None
    
    def _calculate_distance_to_next_stop(self):
        """Calcular distância até próxima paragem"""
        next_sequence = self.current_stop_sequence + 1
        next_stop = self._get_stop_by_sequence(next_sequence)
        
        if next_stop and self.current_stop:
            # Distância em metros entre paragens
            distance_m = next_stop["distance_m"] - self.current_stop["distance_m"]
            self.distance_to_next_stop_km = distance_m / 1000
        else:
            self.distance_to_next_stop_km = 0
    
    def _calculate_distance(self, lat1, lon1, lat2, lon2):
        """Calcular distância entre dois pontos GPS (fórmula de Haversine) em km"""
        R = 6371  # Raio da Terra em km
        
        lat1_rad = math.radians(lat1)
        lat2_rad = math.radians(lat2)
        delta_lat = math.radians(lat2 - lat1)
        delta_lon = math.radians(lon2 - lon1)
        
        a = math.sin(delta_lat/2)**2 + math.cos(lat1_rad) * math.cos(lat2_rad) * math.sin(delta_lon/2)**2
        c = 2 * math.atan2(math.sqrt(a), math.sqrt(1-a))
        
        return R * c
    
    def update(self, delta_time=1.0):
        """
        Atualizar estado do autocarro
        delta_time: tempo decorrido em segundos (padrão: 1s)
        """
        self.time_in_state += delta_time
        
        if self.state == BusState.PARKED:
            # Auto-descarga mínima
            self._discharge(self.SELF_DISCHARGE_RATE * delta_time)
        
        elif self.state == BusState.IDLE_DEPOT:
            # Consumo em idle
            consumption_kw = self.CONSUMPTION_IDLE
            self._discharge((consumption_kw / 3600) * delta_time)
        
        elif self.state == BusState.CHARGING:
            # A carregar
            if self.charging_power_kw > 0:
                energy_added = (self.charging_power_kw / 3600) * delta_time
                self.battery_kwh = min(self.BATTERY_CAPACITY_KWH, self.battery_kwh + energy_added)
                self.battery_percent = (self.battery_kwh / self.BATTERY_CAPACITY_KWH) * 100
                
                # Temperatura aumenta durante carregamento
                self.battery_temperature = min(45, self.battery_temperature + 0.01 * delta_time)
        
        elif self.state == BusState.ROUTE:
            # Em rota - simular movimento
            self._simulate_route_movement(delta_time)
        
        elif self.state == BusState.IDLE_ON_ROUTE:
            # Parado numa paragem
            consumption_kw = self.CONSUMPTION_IDLE
            self._discharge((consumption_kw / 3600) * delta_time)
            
            # Arrefecer ligeiramente
            self.battery_temperature = max(20, self.battery_temperature - 0.02 * delta_time)
        
        elif self.state == BusState.RETURNING:
            # A regressar ao depósito
            self._simulate_return_to_depot(delta_time)
    
    def _simulate_route_movement(self, delta_time):
        """Simular movimento na rota"""
        if self.current_stop_sequence >= self.route["total_stops"]:
            # Rota completa
            self.state = BusState.IDLE_DEPOT
            self.speed_kmh = 0
            return
        
        # Velocidade aleatória entre 20-40 km/h
        self.speed_kmh = random.uniform(20, 40)
        
        # Distância percorrida neste update
        distance_km = (self.speed_kmh / 3600) * delta_time
        
        # Consumo por distância
        consumption_kwh = distance_km * self.CONSUMPTION_ROUTE_KWH_PER_KM
        self._discharge(consumption_kwh)
        
        # Temperatura aumenta durante movimento
        self.battery_temperature = min(35, self.battery_temperature + 0.01 * delta_time)
        
        # Atualizar posição GPS (interpolação simples)
        next_stop = self._get_stop_by_sequence(self.current_stop_sequence + 1)
        if next_stop and self.current_stop:
            progress = min(1.0, distance_km / self.distance_to_next_stop_km if self.distance_to_next_stop_km > 0 else 1.0)
            
            self.latitude += (next_stop["latitude"] - self.current_stop["latitude"]) * progress * 0.1
            self.longitude += (next_stop["longitude"] - self.current_stop["longitude"]) * progress * 0.1
            
            self.distance_to_next_stop_km -= distance_km
            
            # Chegou à próxima paragem?
            if self.distance_to_next_stop_km <= 0:
                self._arrive_at_next_stop()
    
    def _arrive_at_next_stop(self):
        """Chegar à próxima paragem"""
        self.current_stop_sequence += 1
        self.current_stop = self._get_stop_by_sequence(self.current_stop_sequence)
        
        if self.current_stop:
            self.latitude = self.current_stop["latitude"]
            self.longitude = self.current_stop["longitude"]
            
            print(f"[{self.device_id}] Chegou a: {self.current_stop['stop_name']} "
                  f"(Paragem {self.current_stop_sequence}/{self.route['total_stops']}) - "
                  f"Bateria: {self.battery_percent:.1f}%")
        
        # Última paragem?
        if self.current_stop_sequence >= self.route["total_stops"]:
            print(f"[{self.device_id}] Rota completa! Pronto para regressar ao depósito.")
            self.state = BusState.IDLE_ON_ROUTE
            self.speed_kmh = 0
        else:
            # Parar brevemente na paragem (10-20s)
            if random.random() < 0.7:  # 70% de probabilidade de parar
                self.state = BusState.IDLE_ON_ROUTE
                self.speed_kmh = 0
            
            # Calcular distância até próxima
            self._calculate_distance_to_next_stop()
    
    def _simulate_return_to_depot(self, delta_time):
        """Simular regresso ao depósito"""
        # Velocidade constante
        self.speed_kmh = 30
        distance_km = (self.speed_kmh / 3600) * delta_time
        
        # Consumo
        consumption_kwh = distance_km * self.CONSUMPTION_ROUTE_KWH_PER_KM
        self._discharge(consumption_kwh)
        
        # Calcular distância ao depósito
        depot_lat = 41.183580
        depot_lon = -8.618978
        distance_to_depot = self._calculate_distance(self.latitude, self.longitude, depot_lat, depot_lon)
        
        if distance_to_depot < 0.1:  # Chegou (menos de 100m)
            self.latitude = depot_lat
            self.longitude = depot_lon
            self.state = BusState.IDLE_DEPOT
            self.speed_kmh = 0
            print(f"[{self.device_id}] Chegou ao depósito - Bateria: {self.battery_percent:.1f}%")
        else:
            # Mover em direção ao depósito (interpolação simples)
            progress = min(0.01, distance_km / distance_to_depot)
            self.latitude += (depot_lat - self.latitude) * progress
            self.longitude += (depot_lon - self.longitude) * progress
    
    def _discharge(self, kwh):
        """Descarregar bateria"""
        self.battery_kwh = max(0, self.battery_kwh - kwh)
        self.battery_percent = (self.battery_kwh / self.BATTERY_CAPACITY_KWH) * 100
    
    def start_charging(self, charger_id, max_power_kw):
        """Iniciar carregamento"""
        if self.state in [BusState.IDLE_DEPOT, BusState.PARKED]:
            self.state = BusState.CHARGING
            self.connected_charger_id = charger_id
            self.charging_power_kw = min(max_power_kw, 150)
            self.speed_kmh = 0
            print(f"[{self.device_id}] Iniciou carregamento em {charger_id} - {self.charging_power_kw:.1f} kW")
            return True
        return False
    
    def stop_charging(self):
        """Parar carregamento"""
        if self.state == BusState.CHARGING:
            print(f"[{self.device_id}] Parou carregamento - Bateria: {self.battery_percent:.1f}%")
            self.state = BusState.IDLE_DEPOT
            self.connected_charger_id = None
            self.charging_power_kw = 0
            return True
        return False
    
    def continue_route(self):
        """Continuar rota (após paragem)"""
        if self.state == BusState.IDLE_ON_ROUTE and self.current_stop_sequence < self.route["total_stops"]:
            self.state = BusState.ROUTE
            self.time_in_state = 0
            return True
        return False
    
    def return_to_depot(self):
        """Regressar ao depósito"""
        if self.state in [BusState.IDLE_ON_ROUTE, BusState.ROUTE]:
            self.state = BusState.RETURNING
            print(f"[{self.device_id}] A regressar ao depósito...")
            return True
        return False
    
    def get_telemetry(self):
        """Obter telemetria para enviar ao IoT Central"""
        return {
            "batteryKwh": round(self.battery_kwh, 2),
            "batteryLevel": round(self.battery_percent, 2),
            "batteryTemperature": round(self.battery_temperature, 2),
            "latitude": round(self.latitude, 6),
            "longitude": round(self.longitude, 6),
            "state": self.state.value
        }
    
    def get_route_progress(self):
        """Obter progresso na rota"""
        return {
            "route_id": self.route["route_id"],
            "route_name": self.route["route_long_name"],
            "current_stop": self.current_stop_sequence,
            "total_stops": self.route["total_stops"],
            "stops_remaining": self.route["total_stops"] - self.current_stop_sequence,
            "current_stop_name": self.current_stop["stop_name"] if self.current_stop else "N/A"
        }
