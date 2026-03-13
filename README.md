# STCP - Simulação de Carregamento de Autocarros Elétricos

Projeto de simulação realista do sistema de carregamento de autocarros elétricos do STCP Porto.

---

## Versões + Data

## v1

### **v1-basic** - Simulador Básico
Simulador genérico com algoritmo de otimização baseado em prioridades.

📂 [Ver documentação](./v1-basic/README.md)

**Características:**
- Rotas genéricas (Rota-700, Rota-800, Rota-900)
- Algoritmo de otimização inteligente
- Integração Azure IoT Central + Databricks
- 3 autocarros + 3 estações

---


## Executar

### Versão Básica (v1)
```bash
cd v1-basic
python main_realistic.py
```

### Versão GTFS Real (v2) - Recomendado
```bash
cd v2-gtfs-real
python main_gtfs_scenario.py
```

---

## Configuração

1. Copiar `.env.example` para `.env`
2. Preencher credenciais Azure IoT Central
3. Instalar dependências: `pip install -r requirements.txt`

---

## Arquitetura
```
Python Simuladores → Azure IoT Central → Event Hub → Databricks
```

**Componentes:**
- Azure IoT Central (Trial)
- Azure Event Hub (Student)
- Databricks Community Edition
- Python 3.8+

---

## Estrutura do Projeto
```
stcp-bus-charging-simulation/
├── v1-basic/              Versão inicial
├── v2-gtfs-real/          Versão com dados reais (atual)
├── config.py              Configuração partilhada
├── requirements.txt       Dependências Python
└── README.md             Este ficheiro
```

---

## Links

- **GitHub**: https://github.com/Highleaf2/stcp-bus-charging-simulation
- **Databricks Notebook**: [STCP_Event_Hub_Reader]

---

Projeto académico - ISCAP 2026
