graph TB
    subgraph "SENSORES E SIMULADORES"
        A[Sensores Autocarro]
        A1[Bateria kWh/Level]
        A2[Temperatura C]
        A3[GPS Lat/Long]
        A4[Estado PARKED/CHARGING/ROUTE]
        A --> A1 & A2 & A3 & A4
    end
    
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
