# STCP - Diagramas de Workflow

Sistema de Otimização de Carregamento de Autocarros Elétricos

---

## 1. Pipeline Completo do Sistema

Fluxo end-to-end desde sensores até decisões:

```mermaid
graph TB
    subgraph "SENSORES E SIMULADORES"
        A[Sensores Autocarro]
        A1[Bateria kWh/Level]
        A2[Temperatura C]
        A3[GPS Lat/Long]
        A4[Estado PARKED/CHARGING/ROUTE]
        A --> A1 & A2 & A3 & A4
    end
```
    
    subgraph "CLOUD - AZURE IoT CENTRAL"
        B[IoT Central<br/>Device Provisioning]
        B --> C[Data Export]
    end
    
    subgraph "STREAMING - EVENT HUB"
        C --> D[Event Hub<br/>Kafka Protocol]
        D --> D1[Partition 1<br/>stcp-telemetry]
    end
    
    subgraph "PROCESSAMENTO - DATABRICKS"
        D1 --> E[Spark Streaming]
        E --> F[Parse JSON]
        F --> G{Tipo Dispositivo?}
        G -->|BUS-*| H[Bus Telemetry]
        G -->|CS-*| I[Charger Telemetry]
        H --> J[(Delta Table<br/>bus_telemetry)]
        I --> K[(Delta Table<br/>charger_telemetry)]
    end
    
    subgraph "OTIMIZAÇÃO - ALGORITMO"
        L[Charging Scheduler]
        M[Ler Estado Atual]
        N[Calcular Score de Urgência]
        
        M --> N
        J -.Consulta.-> M
        K -.Consulta.-> M
        
        N --> O{Score >= 70?}
        O -->|Sim URGENTE| P[Prioridade Máxima]
        O -->|Não| Q{Score >= 50?}
        Q -->|Sim| R[Prioridade Alta]
        Q -->|Não| S[Prioridade Normal]
    end
    
    subgraph "DECISÕES"
        P & R & S --> T{Bateria<br/>Suficiente?}
        T -->|Não| U{Estação<br/>Disponível?}
        T -->|Sim| V[READY<br/>Pronto para rota]
        
        U -->|Sim| W[START_CHARGING<br/>Conectar estação]
        U -->|Não| X[WAIT<br/>Fila de espera]
    end
    
    style A fill:#4CAF50
    style B fill:#2196F3
    style D fill:#FF9800
    style E fill:#9C27B0
    style L fill:#F44336
```

---

## 2. Algoritmo de Decisão (Detalhado)

Lógica completa do otimizador:

```mermaid
flowchart TD
    Start([A cada 30 segundos]) --> GetData[Obter Estado de<br/>Todos Autocarros]
    GetData --> Loop{Para cada<br/>Autocarro}
    Loop --> GetRoute[Obter Rota Atribuída]
    GetRoute --> CalcScore[Calcular Score]
    
    subgraph "Cálculo de Score"
        CalcScore --> P[Prioridade da Rota]
        CalcScore --> T[Tempo até Partida]
        CalcScore --> B[Défice de Bateria]
        
        P --> P1[Crítica = 40 pts<br/>Alta = 30 pts<br/>Normal = 20 pts]
        T --> T1[Menor 60min = 30 pts<br/>60-120min = 0-30 pts<br/>Maior 120min = 0 pts]
        B --> B1[Bateria menor Necessária = 30 pts<br/>Entre Necessária-Ideal = 0-30 pts<br/>Maior igual Ideal = 0 pts]
        
        P1 & T1 & B1 --> Total[SCORE TOTAL<br/>Máximo 100 pontos]
    end
    
    Total --> Sort[Ordenar por Score<br/>Maior para Menor]
    Sort --> CheckBat{Bateria<br/>Suficiente?}
    
    CheckBat -->|Sim| Ready[READY<br/>Pronto para partir]
    CheckBat -->|Não| CheckState{Estado<br/>Atual?}
    
    CheckState -->|CHARGING| CheckFull{Bateria<br/>Cheia?}
    CheckFull -->|Sim| Stop[STOP_CHARGING<br/>Desconectar]
    CheckFull -->|Não| Continue[CONTINUE_CHARGING<br/>Manter carga]
    
    CheckState -->|Outro| CheckAvail{Estação<br/>Disponível?}
    CheckAvail -->|Sim| Alloc[Alocar Estação]
    CheckAvail -->|Não| Wait[WAIT<br/>Entrar em fila]
    
    Alloc --> StartChg[START_CHARGING<br/>Conectar à estação]
    
    Ready --> Log[Registar Decisão]
    Stop --> Log
    Continue --> Log
    StartChg --> Log
    Wait --> Log
    
    Log --> More{Mais<br/>Autocarros?}
    More -->|Sim| Loop
    More -->|Não| Apply[Aplicar Todas<br/>as Decisões]
    
    Apply --> SendTelem[Enviar Telemetria<br/>Atualizada]
    SendTelem --> Sleep[Aguardar 30s]
    Sleep --> Start
    
    style Start fill:#4CAF50
    style Ready fill:#00BCD4
    style StartChg fill:#4CAF50
    style Wait fill:#FF9800
    style Stop fill:#F44336
    style Continue fill:#2196F3
    style Total fill:#9C27B0
```

---

## 3. Estados do Autocarro

Máquina de estados com todas as transições:

```mermaid
stateDiagram-v2
    [*] --> PARKED: Inicialização
    
    PARKED --> IDLE_DEPOT: Sistema ligado
    PARKED --> PARKED: Self-discharge<br/>0.3% por hora
    
    IDLE_DEPOT --> CHARGING: Bateria insuficiente<br/>Estação disponível
    IDLE_DEPOT --> ROUTE: Bateria OK<br/>Hora de partida
    IDLE_DEPOT --> IDLE_DEPOT: Consumo 2-3 kW
    
    CHARGING --> CHARGING: Bateria menor 95%<br/>Carregando 50-150 kW
    CHARGING --> IDLE_DEPOT: Bateria suficiente<br/>Desconectar
    
    ROUTE --> ROUTE: Consumo 1.5 kWh/km<br/>Velocidade 20-40 km/h
    ROUTE --> IDLE_ON_ROUTE: Parar em sinal/paragem
    ROUTE --> IDLE_DEPOT: Fim da rota<br/>Regressar ao depósito
    
    IDLE_ON_ROUTE --> ROUTE: Retomar viagem<br/>Após 20 segundos
    IDLE_ON_ROUTE --> IDLE_ON_ROUTE: Consumo 2-3 kW
    
    note right of PARKED
        Estado inicial
        Sistemas desligados
    end note
    
    note right of CHARGING
        Temperatura aumenta
        Potência varia com
        nível de bateria
    end note
    
    note right of ROUTE
        GPS muda
        Bateria desce
        Temperatura aumenta
    end note
```

---

## 4. Arquitetura Azure

Componentes cloud e integrações:

```mermaid
graph LR
    subgraph "LOCAL"
        A[Python Simulators<br/>bus_simulator.py<br/>charger_simulator.py]
    end
    
    subgraph "AZURE - TRIAL ACCOUNT"
        B[IoT Central<br/>Device Templates<br/>Data Export Rules]
    end
    
    subgraph "AZURE - STUDENT ACCOUNT"
        C[Event Hub Namespace<br/>ehns-stcp-bus]
        D[Event Hub<br/>stcp-telemetry<br/>Kafka Port 9093]
        E[Databricks Workspace<br/>Spark Streaming]
        F[(Delta Tables<br/>bus_telemetry<br/>charger_telemetry)]
    end
    
    A -->|MQTT/DPS<br/>Telemetria| B
    B -->|Data Export<br/>JSON| C
    C --> D
    D -->|Kafka Protocol<br/>SASL_SSL| E
    E -->|Parse & Store| F
    
    subgraph "ANÁLISE"
        G[SQL Queries]
        H[Visualizações]
        I[Algoritmo Otimização]
    end
    
    F --> G & H & I
    
    style A fill:#4CAF50
    style B fill:#2196F3
    style D fill:#FF9800
    style E fill:#9C27B0
    style I fill:#F44336
```

---

## 5. Timeline de Eventos

Exemplo de execução ao longo do tempo:

```mermaid
gantt
    title STCP - Timeline de Carregamento e Rotas
    dateFormat HH:mm
    axisFormat %H:%M
    
    section BUS-001 (Rota-700)
    Carregamento      :active, b1c, 07:00, 1h
    Pronto            :b1r, 08:00, 30m
    Rota-700 (45km)   :crit, b1d, 08:30, 1.5h
    Regresso          :b1b, 10:00, 30m
    
    section BUS-002 (Rota-800)
    Pronto            :b2r, 07:00, 2h
    Rota-800 (38km)   :b2d, 09:00, 1.25h
    Regresso          :b2b, 10:15, 30m
    
    section BUS-003 (Rota-900)
    Carregamento      :active, b3c, 07:00, 45m
    Rota-900 (52km)   :crit, b3d, 07:45, 1.75h
    Regresso          :b3b, 09:30, 30m
    Carregamento      :active, b3c2, 10:00, 1h
    
    section Estações
    CS-001 ocupada    :active, c1, 07:00, 1h
    CS-002 disponível :done, c2, 07:00, 12h
    CS-003 ocupada    :active, c3, 07:00, 45m
    CS-003 ocupada    :active, c3b, 10:00, 1h
```

---

## Legenda

### Cores
- Verde: Componentes ativos/processamento
- Azul: Serviços cloud
- Laranja: Streaming de dados
- Roxo: Análise e transformação
- Vermelho: Decisões e otimização

### Estados do Sistema
- READY - Pronto para iniciar rota
- CHARGING - Em carregamento
- WAIT - Em fila de espera
- ROUTE - Em rota operacional
- PARKED - Estacionado no depósito

---

Projeto académico - STCP Bus Charging Optimization  
Fevereiro 2026
```
