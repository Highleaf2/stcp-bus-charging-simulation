## 1. Pipeline Completo do Sistema

Fluxo end-to-end desde sensores até decisões:
```mermaid
graph LR
    subgraph SENSORES["SENSORES E TELEMETRIA"]
        A[Sensores<br/>Autocarro]
        CS[Sensores<br/>Estações]
    end
    
    A --> A1[Bateria kWh/Level]
    A --> A2[Temperatura C]
    A --> A3[GPS Lat/Long]
    A --> A4[Estado]
    
    CS --> CS1[Temp Carregador]
    CS --> CS2[Potência kW]
    CS --> CS3[Energia kWh]
    CS --> CS4[Estado]
    
    A1 --> B
    A2 --> B
    A3 --> B
    A4 --> B
    CS1 --> B
    CS2 --> B
    CS3 --> B
    CS4 --> B
    
    B[IoT Central] --> C[Data Export]
    C --> D[Event Hub]
    D --> E[Spark Streaming]
    E --> F[Parse JSON]
    F --> G{Tipo?}
    
    G -->|BUS| H[Bus Telemetry]
    G -->|CS| I[Charger Telemetry]
    
    H --> J[(Delta Table<br/>bus_telemetry)]
    I --> K[(Delta Table<br/>charger_telemetry)]
    
    J --> M[Ler Estado]
    K --> M
    M --> N[Calcular Score]
    
    N --> O{Score >= 70?}
    O -->|Sim| P[Prioridade Max]
    O -->|Não| Q{Score >= 50?}
    Q -->|Sim| R[Prioridade Alta]
    Q -->|Não| S[Prioridade Normal]
    
    P --> T{Bateria OK?}
    R --> T
    S --> T
    
    T -->|Não| U{Estação Livre?}
    T -->|Sim| V[READY]
    
    U -->|Sim| W[START_CHARGING]
    U -->|Não| X[WAIT]
    
    W --> Y[Atualizar]
    X --> Y
    V --> Y
    
    Y --> ZB[Telemetria Autocarros]
    Y --> ZC[Telemetria Estações]
    ZB --> A
    ZC --> CS
    
    style A fill:#4CAF50
    style CS fill:#4CAF50
    style B fill:#2196F3
    style D fill:#FF9800
    style E fill:#9C27B0
    style N fill:#F44336
```
