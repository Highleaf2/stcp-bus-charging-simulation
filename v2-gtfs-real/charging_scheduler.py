"""
Otimizador de Carregamento - STCP
Decide quando e onde cada autocarro deve carregar baseado em:
- Prioridade da rota
- Tempo até partida
- Nível de bateria atual
- Disponibilidade de estações
"""

from datetime import datetime
import routes_config as routes

class ChargingScheduler:
    """
    Otimizador que decide estratégia de carregamento
    para maximizar disponibilidade e respeitar prioridades
    """
    
    def __init__(self):
        self.charging_decisions = {}  # Histórico de decisões
        self.last_optimization_time = None
    
    def calculate_urgency_score(self, bus_id, bus_state, current_time):
        """
        Calcular score de urgência para um autocarro
        Score mais alto = mais urgente carregar
        
        Fatores:
        - Prioridade da rota (40%)
        - Tempo até partida (30%)
        - Défice de bateria (30%)
        """
        route_info = routes.get_route_for_bus(bus_id)
        if not route_info:
            return 0
        
        # Fator 1: Prioridade da rota (0-40 pontos)
        priority_level = routes.get_priority_level(route_info["priority"])
        priority_score = priority_level * 10  # Crítica=40, Alta=30, Normal=20, Baixa=10
        
        # Fator 2: Tempo até partida (0-30 pontos)
        # Quanto menos tempo, mais urgente
        try:
            minutes_to_departure = routes.calculate_time_to_departure(
                current_time,
                route_info["departure_time"]
            )
            
            # Se falta menos de 60 min: urgência máxima (30 pontos)
            # Se falta mais de 120 min: urgência mínima (0 pontos)
            if minutes_to_departure <= routes.OPTIMIZATION_CONFIG["charging_urgency_threshold_minutes"]:
                time_score = 30
            elif minutes_to_departure >= routes.OPTIMIZATION_CONFIG["preferred_charge_time_before_departure_minutes"]:
                time_score = 0
            else:
                # Interpolar entre 0 e 30
                range_minutes = (routes.OPTIMIZATION_CONFIG["preferred_charge_time_before_departure_minutes"] - 
                               routes.OPTIMIZATION_CONFIG["charging_urgency_threshold_minutes"])
                relative_urgency = 1 - ((minutes_to_departure - 60) / range_minutes)
                time_score = relative_urgency * 30
        except:
            time_score = 0
        
        # Fator 3: Défice de bateria (0-30 pontos)
        # Quanto mais abaixo da bateria necessária, mais urgente
        battery_percent = bus_state.get("battery_percent", 100)
        required_percent = route_info["required_battery_percent"]
        buffer = routes.OPTIMIZATION_CONFIG["min_battery_buffer_percent"]
        target_battery = required_percent + buffer
        
        if battery_percent >= target_battery:
            battery_score = 0  # Já tem bateria suficiente
        elif battery_percent < required_percent:
            battery_score = 30  # Abaixo do mínimo necessário - urgente!
        else:
            # Entre necessário e ideal
            deficit = target_battery - battery_percent
            battery_score = (deficit / buffer) * 30
        
        # Score total
        total_score = priority_score + time_score + battery_score
        
        return {
            "total_score": total_score,
            "priority_score": priority_score,
            "time_score": time_score,
            "battery_score": battery_score,
            "route": route_info["description"],
            "minutes_to_departure": minutes_to_departure if 'minutes_to_departure' in locals() else None,
            "battery_deficit": target_battery - battery_percent
        }
    
    def optimize_charging_schedule(self, buses, chargers, current_time):
        """
        Determinar estratégia ótima de carregamento
        
        Retorna:
        {
            "BUS-001": {
                "action": "START_CHARGING" | "CONTINUE_CHARGING" | "STOP_CHARGING" | "WAIT",
                "charger": "CS-001" | None,
                "reason": "Rota crítica com partida em 45 min",
                "urgency_score": 85.3
            },
            ...
        }
        """
        decisions = {}
        
        # 1. Calcular urgência de todos os autocarros
        bus_urgencies = []
        for bus_id, bus in buses.items():
            urgency = self.calculate_urgency_score(
                bus_id,
                {
                    "battery_percent": bus.battery_percent,
                    "state": bus.state.value
                },
                current_time
            )
            urgency["bus_id"] = bus_id
            urgency["current_state"] = bus.state.value
            urgency["battery_percent"] = bus.battery_percent
            bus_urgencies.append(urgency)
        
        # 2. Ordenar por urgência (maior score primeiro)
        bus_urgencies.sort(key=lambda x: x["total_score"], reverse=True)
        
        # 3. Verificar estações disponíveis
        available_chargers = [
            charger_id for charger_id, charger in chargers.items()
            if charger.state == "IDLE"
        ]
        
        # 4. Autocarros já a carregar (continuam)
        buses_currently_charging = [
            bus_urgency for bus_urgency in bus_urgencies
            if bus_urgency["current_state"] == "CHARGING"
        ]
        
        # 5. Tomar decisões
        chargers_allocated = 0
        
        for bus_urgency in bus_urgencies:
            bus_id = bus_urgency["bus_id"]
            bus = buses[bus_id]
            route_info = routes.get_route_for_bus(bus_id)
            
            # Autocarro já a carregar
            if bus_urgency["current_state"] == "CHARGING":
                # Verificar se já tem bateria suficiente
                if routes.is_battery_sufficient_for_route(bus.battery_percent, route_info):
                    decisions[bus_id] = {
                        "action": "STOP_CHARGING",
                        "charger": None,
                        "reason": f"Bateria suficiente ({bus.battery_percent:.1f}%) para {route_info['description']}",
                        "urgency_score": bus_urgency["total_score"]
                    }
                else:
                    decisions[bus_id] = {
                        "action": "CONTINUE_CHARGING",
                        "charger": bus.connected_charger_id,
                        "reason": f"Continuar até atingir bateria necessária ({route_info['required_battery_percent']:.1f}%)",
                        "urgency_score": bus_urgency["total_score"]
                    }
                chargers_allocated += 1
            
            # Autocarro precisa carregar
            elif not routes.is_battery_sufficient_for_route(bus.battery_percent, route_info):
                # Verificar se há estações disponíveis
                if available_chargers and chargers_allocated < routes.OPTIMIZATION_CONFIG["max_charging_sessions_simultaneous"]:
                    # Alocar próxima estação disponível
                    charger_id = available_chargers.pop(0)
                    
                    # Motivo detalhado
                    if bus_urgency["total_score"] >= 70:
                        urgency_text = "URGENTE"
                    elif bus_urgency["total_score"] >= 50:
                        urgency_text = "PRIORITÁRIO"
                    else:
                        urgency_text = "NORMAL"
                    
                    reason_parts = [
                        f"{urgency_text}:",
                        route_info["description"],
                        f"Partida em {bus_urgency['minutes_to_departure']:.0f} min" if bus_urgency["minutes_to_departure"] else "",
                        f"Bateria atual: {bus.battery_percent:.1f}%",
                        f"Necessário: {route_info['required_battery_percent']:.1f}%"
                    ]
                    
                    decisions[bus_id] = {
                        "action": "START_CHARGING",
                        "charger": charger_id,
                        "reason": " | ".join([p for p in reason_parts if p]),
                        "urgency_score": bus_urgency["total_score"]
                    }
                    chargers_allocated += 1
                else:
                    # Sem estações disponíveis - entrar em fila de espera
                    decisions[bus_id] = {
                        "action": "WAIT",
                        "charger": None,
                        "reason": f"Aguardar disponibilidade de estação (urgência: {bus_urgency['total_score']:.1f})",
                        "urgency_score": bus_urgency["total_score"]
                    }
            
            # Autocarro com bateria suficiente
            else:
                decisions[bus_id] = {
                    "action": "READY",
                    "charger": None,
                    "reason": f"Pronto para rota {route_info['description']} ({bus.battery_percent:.1f}% disponível)",
                    "urgency_score": 0
                }
        
        self.charging_decisions = decisions
        self.last_optimization_time = current_time
        
        return decisions
    
    def get_optimization_summary(self):
        """Obter resumo da última otimização"""
        if not self.charging_decisions:
            return "Nenhuma otimização executada ainda"
        
        summary_lines = [
            "\n" + "="*80,
            "DECISÕES DO ALGORITMO DE OTIMIZAÇÃO",
            "="*80
        ]
        
        # Ordenar por urgência
        sorted_decisions = sorted(
            self.charging_decisions.items(),
            key=lambda x: x[1]["urgency_score"],
            reverse=True
        )
        
        for bus_id, decision in sorted_decisions:
            summary_lines.append(
                f"[{bus_id}] {decision['action']:20s} | "
                f"Score: {decision['urgency_score']:5.1f} | "
                f"{decision['reason']}"
            )
        
        summary_lines.append("="*80 + "\n")
        
        return "\n".join(summary_lines)
