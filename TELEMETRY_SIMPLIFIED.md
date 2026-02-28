# Telemetria Simplificada - Autocarros

## ✅ O Que Foi Alterado

### **Telemetria dos Autocarros (Antes)**
```json
{
  "batteryKwh": 214.3,
  "batteryLevel": 61.2,
  "batteryTemperature": 26.4,
  "instantConsumption": 82.3,
  "latitude": 41.1781,
  "longitude": -8.6081,
  "remainingRange": 178.4,
  "state": "ROUTE",
  "speed": 35.2,
  "charging": false
}
```

### **Telemetria dos Autocarros (Agora - Simplificada)**
```json
{
  "batteryKwh": 214.3,
  "batteryLevel": 61.2,
  "batteryTemperature": 26.4,
  "latitude": 41.1781,
  "longitude": -8.6081,
  "state": "ROUTE"
}
```

---

## 📊 Variáveis Mantidas

| Variável | Descrição | Porquê |
|----------|-----------|--------|
| `batteryKwh` | Energia na bateria (kWh) | Saber capacidade real |
| `batteryLevel` | Bateria em percentagem (%) | Saber estado de carga |
| `batteryTemperature` | Temperatura bateria (°C) | Monitorizar saúde |
| `latitude` | Coordenada GPS | Localizar autocarro |
| `longitude` | Coordenada GPS | Localizar autocarro |
| `state` | Estado operacional | Saber o que está a fazer |

### **Estados Possíveis**
- `PARKED` - Desligado no depósito
- `IDLE_DEPOT` - Ligado no depósito
- `CHARGING` - A carregar
- `ROUTE` - Em rota
- `IDLE_ON_ROUTE` - Parado em paragem/sinal

---

## ❌ Variáveis Removidas

| Variável | Porquê Remover |
|----------|----------------|
| `instantConsumption` | Não necessário para análise básica |
| `remainingRange` | Pode ser calculado: `batteryKwh / 1.5` |
| `speed` | Não necessário |
| `charging` | Redundante (já está em `state`) |

---

## 🔧 O Que Continua a Funcionar

**Internamente**, os simuladores **ainda calculam tudo**:
- ✅ Consumo realista
- ✅ Self-discharge
- ✅ Carregamento com curva
- ✅ Temperatura reactiva
- ✅ Movimento GPS
- ✅ Velocidade

**Apenas não envia** essas variáveis extras para o IoT Central e Databricks.

---

## 📈 Exemplo de Logs

### **Consola**
```
[BUS-001] CHARGING - Battery: 68.2% (238.7 kWh) - Temp: 29.3°C - Location: (41.1781, -8.6081)
[BUS-002] ROUTE - Battery: 57.4% (200.9 kWh) - Temp: 25.8°C - Location: (41.1795, -8.6095)
[BUS-003] IDLE_ON_ROUTE - Battery: 51.3% (179.6 kWh) - Temp: 23.1°C - Location: (41.1802, -8.6110)
```

### **IoT Central / Databricks**
Vais receber apenas 6 campos por autocarro, em vez de 10.

---

## 📝 Ficheiros Atualizados

- ✅ `bus_simulator.py` - método `get_telemetry()` simplificado
- ✅ `main_realistic.py` - logs atualizados
- ⚪ `charger_simulator.py` - sem alterações

---

## 🚀 Próximo Passo

1. Substitui os 2 ficheiros no teu projeto
2. Executa: `python main_realistic.py`
3. Vê telemetria simplificada!

---

**Nota**: Se mais tarde precisares de adicionar variáveis, é só descomentar no código!
