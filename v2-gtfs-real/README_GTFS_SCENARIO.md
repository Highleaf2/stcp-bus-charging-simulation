# STCP - Simulação com Cenário GTFS Real

Simulação de autocarros elétricos usando **rotas reais** do STCP Porto com estados iniciais específicos.

---

## Ficheiros Criados

1. **gtfs_routes.py** - Rotas GTFS completas (200, 201, 202)
2. **bus_simulator_gtfs.py** - Simulador com rotas reais
3. **main_gtfs_scenario.py** - Orquestrador principal

---

## Estado Inicial (Configurado)

### **Autocarros**

| ID | Bateria | Rota | Paragem Atual | Estado |
|----|---------|------|---------------|--------|
| BUS-001 | 30% (105 kWh) | 200 (Bolhão - Castelo Queijo) | 25/30 (Crasto) | Ainda faltam 5 paragens |
| BUS-002 | 70% (245 kWh) | 201 (Aliados - Viso) | 2/26 (Trindade) | Na segunda paragem |
| BUS-003 | 25% (87.5 kWh) | 202 (Aliados - Passeio Alegre) | 16/16 (Passeio Alegre) | A terminar a rota |

### **Rotas**

**Rota 200**: Bolhão → Castelo do Queijo (9.85 km, 30 paragens)
**Rota 201**: Aliados → Viso (9.78 km, 26 paragens)
**Rota 202**: Aliados → Passeio Alegre (5.31 km, 16 paragens)

### **Estações**

Todas no depósito STCP:
- **Latitude**: 41.183580
- **Longitude**: -8.618978

---

## Como Funciona

### **1. Simulação de Movimento**

Os autocarros:
- ✅ Seguem rotas GTFS reais paragem a paragem
- ✅ Velocidade realista (20-40 km/h)
- ✅ Param em cada paragem (10-20s)
- ✅ Atualizam GPS em tempo real
- ✅ Consomem bateria (1.5 kWh/km)

### **2. Estados Possíveis**

```
PARKED → Estacionado no depósito
IDLE_DEPOT → No depósito, sistemas ligados
CHARGING → A carregar
ROUTE → Em rota (a andar)
IDLE_ON_ROUTE → Parado na paragem
RETURNING → A regressar ao depósito
```

### **3. Fluxo Automático**

```
Início → Em rota (paragem X)
  ↓
Chegar a cada paragem
  ↓
Parar 10-20s
  ↓
Continuar até fim da rota
  ↓
Rota completa → Regressar ao depósito
  ↓
No depósito → Algoritmo decide se carregar
  ↓
Carregar até bateria suficiente
```

---

## Executar

### **Passo 1: Verificar Ficheiros**

Tens os ficheiros necessários?
- ✅ `gtfs_routes.py`
- ✅ `bus_simulator_gtfs.py`
- ✅ `main_gtfs_scenario.py`
- ✅ `charger_simulator.py` (do sistema anterior)
- ✅ `charging_scheduler.py` (do sistema anterior)
- ✅ `config.py` (do sistema anterior)
- ✅ `.env` (credenciais Azure)

### **Passo 2: Executar**

```bash
python main_gtfs_scenario.py
```

### **Passo 3: Ver Logs**

```
================================================================================
STCP SIMULATION - CENÁRIO GTFS REAL
Rotas reais do Porto com estados iniciais específicos
================================================================================

[BUS-001] Inicializado - Rota: 200 | Paragem: 25/30 | Bateria: 30.0% | ...
[BUS-002] Inicializado - Rota: 201 | Paragem: 2/26 | Bateria: 70.0% | ...
[BUS-003] Inicializado - Rota: 202 | Paragem: 16/16 | Bateria: 25.0% | ...

================================================================================
ESTADO ATUAL DO SISTEMA
================================================================================

[BUS-001] Rota 200 - Bolhão - Cast.queijo
  Paragem: 25/30 (Crasto)
  Faltam: 5 paragens
  Bateria: 30.0% (105.0 kWh)
  Estado: ROUTE
  Localização: (41.157713, -8.679766)

...

>>> INICIANDO SIMULAÇÃO COM ROTAS GTFS REAIS <<<
>>> Otimização a cada 30s <<<
```

---

## O Que Vai Acontecer

### **BUS-001** (30% bateria, faltam 5 paragens)
1. Continua rota até Castelo do Queijo
2. Chega com ~25.9% bateria
3. Regressa ao depósito (9.55 km)
4. **Bateria CRÍTICA ao chegar!**
5. Algoritmo prioriza carregamento URGENTE

### **BUS-002** (70% bateria, 2ª paragem)
1. Continua rota até Viso
2. Ainda tem 24 paragens pela frente
3. Chega ao fim com ~65% bateria
4. Regressa ao depósito
5. Bateria OK, pode esperar

### **BUS-003** (25% bateria, rota completa)
1. **JÁ terminou a rota!**
2. Regressa IMEDIATAMENTE ao depósito (6.5 km)
3. Chega com ~22.2% bateria
4. **CRÍTICO! Carrega primeiro!**

### **Algoritmo de Otimização**

```
Score BUS-003: ~95 (Crítico + bateria baixa)
  → Conecta CS-003 IMEDIATAMENTE

Score BUS-001: ~85 (Bateria baixa + será crítico)
  → Conecta CS-001 quando chegar

Score BUS-002: ~20 (Normal + bateria OK)
  → WAIT (pode esperar)
```

---

## Dados no Databricks

### **Telemetria dos Autocarros**

```sql
SELECT 
    device_id,
    date_format(event_time, 'dd-MM-yyyy HH:mm:ss') as data_hora,
    state,
    batteryLevel,
    latitude,
    longitude
FROM bus_telemetry
WHERE device_id = 'BUS-001'
ORDER BY event_time DESC
LIMIT 20
```

**Vais ver**:
- Progressão paragem a paragem
- GPS a mudar ao longo da rota
- Bateria a descer gradualmente
- Estados: ROUTE → IDLE_ON_ROUTE → ROUTE → RETURNING → CHARGING

### **Análises Interessantes**

**1. Ver trajeto completo de um autocarro:**
```sql
SELECT 
    latitude,
    longitude,
    batteryLevel,
    state
FROM bus_telemetry
WHERE device_id = 'BUS-003'
ORDER BY event_time
```

**2. Ver quando chegou a cada paragem:**
```sql
SELECT 
    date_format(event_time, 'HH:mm:ss') as hora,
    ROUND(latitude, 6) as lat,
    ROUND(longitude, 6) as lon,
    batteryLevel
FROM bus_telemetry
WHERE device_id = 'BUS-001'
    AND state = 'IDLE_ON_ROUTE'
ORDER BY event_time
```

**3. Calcular consumo real vs previsto:**
```sql
WITH route_data AS (
    SELECT 
        device_id,
        MIN(batteryLevel) as bateria_final,
        MAX(batteryLevel) as bateria_inicio,
        MAX(batteryLevel) - MIN(batteryLevel) as consumo_percent
    FROM bus_telemetry
    WHERE state IN ('ROUTE', 'IDLE_ON_ROUTE')
    GROUP BY device_id
)
SELECT 
    device_id,
    consumo_percent,
    consumo_percent * 3.5 as consumo_kwh,
    CASE 
        WHEN device_id = 'BUS-001' THEN 9.85
        WHEN device_id = 'BUS-002' THEN 9.78
        WHEN device_id = 'BUS-003' THEN 5.31
    END as distancia_km,
    (consumo_percent * 3.5) / CASE 
        WHEN device_id = 'BUS-001' THEN 9.85
        WHEN device_id = 'BUS-002' THEN 9.78
        WHEN device_id = 'BUS-003' THEN 5.31
    END as consumo_kwh_por_km
FROM route_data
```

---

## Diferenças vs Simulador Anterior

| Característica | Simulador Anterior | Simulador GTFS |
|----------------|-------------------|----------------|
| Rotas | Genéricas (fictícias) | Reais do STCP Porto |
| Paragens | Não tinha | 30/26/16 paragens reais |
| GPS | Aleatório | Coordenadas reais |
| Estado Inicial | Aleatório | Configurado (tua tabela) |
| Movimento | Simulado genérico | Paragem a paragem |
| Distâncias | Aproximadas | Reais (GTFS) |

---

## Próximos Passos

1. **Executar simulação** por 30-60 min
2. **Ver no Databricks** autocarros a moverem-se
3. **Analisar decisões** do algoritmo
4. **Validar** se prioridades estão corretas
5. **Exportar dados** para tese

---

## Troubleshooting

**Erro: `ModuleNotFoundError: No module named 'gtfs_routes'`**
→ Ficheiros têm de estar na mesma pasta

**Erro: `KeyError: 'BUS-001'`**
→ Verifica se `config.py` tem todas as chaves de dispositivos

**Autocarros não se movem**
→ Verifica estado inicial (podem estar IDLE_DEPOT esperando otimização)

**GPS não muda**
→ Autocarro pode estar parado numa paragem (IDLE_ON_ROUTE)

---

## Validação

Testa se funciona:

```python
# Test no terminal Python
from gtfs_routes import ROUTE_200, INITIAL_BUS_STATE
print(ROUTE_200["total_stops"])  # Deve dar 30
print(INITIAL_BUS_STATE["BUS-001"]["battery_percent"])  # Deve dar 30.0
```

---

**Criado para**: Projeto STCP - Simulação com Dados Reais  
**Data**: Março 2026  
**Versão**: 3.0 - Cenário GTFS Real
