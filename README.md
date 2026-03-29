# Diário de Trabalho - Projecto STCP
## Sistema de Monitorização de Carregamento de Autocarros Eléctricos

**Autor:** Luís Pereira  
**Instituição:** ISCAP  
**Ano:** 2026  
**Repositório:** https://github.com/Highleaf2/stcp-bus-charging-simulation  

---

## Índice

1. Contexto e Objectivo do Projecto
2. Arquitectura do Sistema
3. Dispositivos e Telemetria
4. Registo Cronológico do Trabalho
5. Estado Actual do Projecto
6. Passos Seguintes
7. Decisões Técnicas e Justificações

---

## 1. Contexto e Objectivo do Projecto

O projecto tem como objectivo simular e monitorizar em tempo real o sistema de carregamento de autocarros eléctricos da STCP (Sociedade de Transportes Colectivos do Porto). O sistema permite acompanhar o estado da frota - nível de bateria, localização GPS, estado das estações de carregamento - através de dados de telemetria enviados para a nuvem.

A arquitectura foi desenhada para simular, na fase académica, o que em produção seria feito por APIs e sensores reais instalados nos autocarros e nas estações de carregamento. Isto significa que o simulador Python é apenas temporário e substituível, sem necessidade de alterar o resto da arquitectura.

**Foco actual definido pelo orientador:** queries. Ou seja, com os dados a chegar ao Databricks, conseguir responder a perguntas como:
- Qual o nível de bateria do autocarro X?
- Onde está o autocarro Y neste momento?
- Qual a estação de carregamento disponível?
- Qual o estado geral da frota?

---

## 2. Arquitectura do Sistema

O sistema funciona em camadas. Cada camada tem uma responsabilidade específica:

```
[Python Simulador - VS Code] --> [Azure IoT Central] --> [Azure Event Hub] --> [Azure Databricks]
```

**Camada 1 - Simulador Python (PC Local / VS Code)**  
Ficheiros: `charging_station_simulator.py`, `electric_bus_simulator.py`, `main.py`  
Função: Gerar dados simulados de telemetria (bateria, GPS, temperatura, estado) e enviá-los para o Azure IoT Central usando o protocolo MQTT via DPS (Device Provisioning Service).  
Nota: No futuro, esta camada será substituída por APIs reais dos autocarros e estações. A arquitectura não muda.

**Camada 2 - Azure IoT Central (Conta Trial)**  
URL: https://stcp-bus.azureiotcentral.com (exemplo)  
Função: Receber a telemetria de cada dispositivo, gerir a autenticação via DPS, e exportar os dados em tempo real para o Event Hub através de uma regra de exportação de dados.

**Camada 3 - Azure Event Hub (Conta Student)**  
Namespace: `ehns-stcp-bus`  
Nome do Event Hub: `stcp-telemetry`  
Função: Actua como fila de mensagens (message broker). Recebe os dados do IoT Central e disponibiliza-os para o Databricks consumir via protocolo Kafka (porta 9093 com autenticação SASL_SSL).

**Camada 4 - Azure Databricks (Community Edition)**  
Função: Consome o stream de dados do Event Hub, faz o parse do JSON, separa os dados por tipo de dispositivo (autocarros vs estações de carregamento), armazena em tabelas Delta e permite fazer queries SQL em tempo real.

---

## 3. Dispositivos e Telemetria

### 3.1 Autocarros Eléctricos

Foram configurados 3 autocarros no Azure IoT Central:

| ID do Dispositivo | Rota Atribuída | Hora de Partida |
|---|---|---|
| BUS-001 | Route-700 | 08:30 |
| BUS-002 | Route-800 | 09:00 |
| BUS-003 | Route-900 | 07:45 |

**Modelo:** CaetanoBus e.City Gold  
**Capacidade da bateria:** 350 kWh  
**Consumo médio:** 1,2 kWh/km  
**Nível crítico:** 20% (abaixo disto o autocarro não deve sair em rota)  
**Nível ideal:** 80% (acima disto considera-se suficientemente carregado)

**Telemetria enviada por cada autocarro (a cada segundo):**

| Campo | Tipo | Descrição |
|---|---|---|
| batteryLevel | Percentagem (%) | Estado de carga da bateria |
| batteryKwh | Double (kWh) | Energia disponível na bateria |
| batteryTemperature | Double (Celsius) | Temperatura da bateria |
| latitude | Double | Coordenada GPS - latitude |
| longitude | Double | Coordenada GPS - longitude |
| state | Texto | Estado operacional: PARKED, CHARGING, ROUTE, IDLE_ON_ROUTE |

**Estados possíveis de um autocarro:**
- PARKED: Estacionado no depósito, sistemas desligados
- CHARGING: Ligado a uma estação de carregamento, a receber energia
- ROUTE: Em rota activa, a consumir bateria
- IDLE_ON_ROUTE: Parado em sinal ou paragem intermédia

### 3.2 Estações de Carregamento

Foram configuradas 3 estações de carregamento:

| ID do Dispositivo | Potência Máxima |
|---|---|
| CS-001 | 150 kW |
| CS-002 | 150 kW |
| CS-003 | 150 kW |

**Telemetria enviada por cada estação (a cada segundo):**

| Campo | Tipo | Descrição |
|---|---|---|
| state | Texto | Estado: IDLE (livre) ou CHARGING (ocupada) |
| currentPower | Double (kW) | Potência a ser entregue neste momento |
| currentEfficiency | Double (%) | Eficiência actual do carregamento |
| chargerTemperature | Double (Celsius) | Temperatura do equipamento |
| energyDelivered | Double (kWh) | Energia entregue na sessão actual |
| totalEnergyDelivered | Double (kWh) | Energia total entregue desde o início |
| connectedBus | Texto | ID do autocarro ligado (null se livre) |

---

## 4. Registo Cronológico do Trabalho

### Fase 1 - Configuração da Infraestrutura Azure

**O que foi feito:**

Foi criada a conta Azure IoT Central (plano Trial) e configurados os 6 dispositivos - 3 autocarros (BUS-001, BUS-002, BUS-003) e 3 estações de carregamento (CS-001, CS-002, CS-003). Para cada dispositivo foi gerada uma chave primária de autenticação.

Foi criada a conta Azure (plano Student) para o Event Hub. Foi criado um namespace chamado `ehns-stcp-bus` e dentro dele um Event Hub chamado `stcp-telemetry`. Foi configurada uma política de acesso chamada `RootManageSharedAccessKey` que permite leitura e escrita.

No Azure IoT Central foi configurada uma regra de exportação de dados (Data Export) que envia toda a telemetria recebida para o Event Hub em tempo real, no formato JSON.

**Credenciais configuradas (guardadas no ficheiro `.env`):**

```
ID_SCOPE=0ne011270BD
PROVISIONING_HOST=global.azure-devices-provisioning.net
BUS_001_KEY=[chave privada]
BUS_002_KEY=[chave privada]
BUS_003_KEY=[chave privada]
CS_001_KEY=[chave privada]
CS_002_KEY=[chave privada]
CS_003_KEY=[chave privada]
EH_NAMESPACE=ehns-stcp-bus
EH_NAME=stcp-telemetry
EH_KEY_NAME=RootManageSharedAccessKey
EH_KEY=[chave privada]
```

Nota: O ficheiro `.env` não está no repositório GitHub por conter credenciais privadas. Está listado no `.gitignore`.

---

### Fase 2 - Simulador Python (Versão Inicial)

**O que foi feito:**

Foram criados os ficheiros Python que simulam o comportamento dos dispositivos e enviam telemetria para o Azure IoT Central.

**Ficheiro: `charging_station_simulator.py`**  
Contém a classe `ChargingStationSimulator`. Cada instância representa uma estação de carregamento. A classe:
- Liga-se ao Azure IoT Central via DPS (Device Provisioning Service) usando autenticação por chave simétrica
- Envia telemetria a cada segundo: potência actual, temperatura, energia entregue, eficiência
- Simula o comportamento real: temperatura aumenta quando está a carregar, volta à temperatura ambiente quando está livre
- Tem métodos para iniciar e parar sessões de carregamento (`start_charging`, `stop_charging`)

**Ficheiro: `electric_bus_simulator.py`**  
Contém a classe `ElectricBusSimulator`. Cada instância representa um autocarro. A classe:
- Liga-se ao Azure IoT Central da mesma forma que as estações
- Envia telemetria a cada segundo: nível de bateria, kWh, GPS, temperatura, estado
- Simula comportamento realista: bateria desce quando está em rota, sobe quando está a carregar, temperatura reage ao estado
- Simula movimento GPS: coordenadas mudam ligeiramente quando está em rota
- Tem métodos para iniciar carregamento, parar carregamento e iniciar rota

**Ficheiro: `main.py`**  
Orquestrador principal. Cria todas as instâncias (3 estações + 3 autocarros), liga todas ao Azure IoT Central em paralelo usando `asyncio`, e implementa uma lógica básica de carregamento:
- Se bateria do autocarro < 50% e está estacionado, liga a uma estação disponível
- Se bateria >= 90%, desliga o carregamento
- Esta verificação acontece a cada 5 segundos

**Ficheiro: `config.py`**  
Contém a configuração partilhada por todos os ficheiros: lista de dispositivos com os seus IDs e chaves, localização do depósito (latitude/longitude), e intervalo de telemetria.

---

### Fase 3 - Notebooks Azure Databricks

Foram criados 4 notebooks no Azure Databricks Community Edition. Estes notebooks são executados manualmente na plataforma Databricks e processam os dados que chegam do Event Hub.

**Notebook 1: "STCP Dados Simulados"**  
Este é o notebook principal de ingestão de dados. Faz o seguinte:

- Configura a ligação ao Event Hub usando o protocolo Kafka com autenticação SASL_SSL
- Cria um Spark Streaming DataFrame que lê continuamente os dados novos
- Faz o parse do JSON recebido, extraindo os campos de telemetria
- Separa os dados em dois streams: um para autocarros (deviceId começa por "BUS-") e outro para estações (deviceId começa por "CS-")
- Escreve os dados em duas tabelas Delta permanentes: `bus_telemetry` e `charger_telemetry`
- Inclui uma célula de reset que permite limpar tudo e recomeçar

Schema da tabela `bus_telemetry`:
```
device_id          string
event_time         timestamp
batteryLevel       double
batteryKwh         double
batteryTemperature double
latitude           double
longitude          double
state              string
```

Schema da tabela `charger_telemetry`:
```
device_id              string
event_time             timestamp
state                  string
currentPower           double
currentEfficiency      double
chargerTemperature     double
energyDelivered        double
totalEnergyDelivered   double
connectedBus           string
```

**Notebook 2: "STCP Business Rules"**  
Contém 8 regras de negócio implementadas como queries SQL sobre as tabelas Delta. Estas regras definem os limites e critérios do sistema:
- Regra 1: Limites de potência (máximo 150 kW por estação, bateria máxima 350 kWh)
- Regra 2: Prioridades de carregamento (nível crítico: 20%, nível ideal: 80%)
- Regra 3: Limites de temperatura (temperatura máxima da bateria e do carregador)
- Regra 4: Disponibilidade de estações
- Regra 5: Distância ao depósito
- Regra 6: Tempo estimado de carregamento
- Regra 7: Balanceamento de carga entre estações
- Regra 8: Saúde da bateria

**Notebook 3: "STCP Algoritmo de Decisão"**  
Algoritmo inteligente que combina as 8 regras de negócio para decidir automaticamente qual autocarro carregar, em qual estação, e com que potência. Calcula um "score de urgência" para cada autocarro (máximo 100 pontos) com base em:
- Prioridade da rota (até 40 pontos)
- Tempo até à partida (até 30 pontos)
- Défice de bateria face ao necessário (até 30 pontos)

**Notebook 4: "STCP Simulação de Cenários"**  
Permite testar diferentes cenários manualmente para validar o comportamento do sistema.

---

### Fase 4 - Simplificação por indicação do orientador (ESTADO ACTUAL)

**Decisão do orientador:**  
O orientador indicou que o foco actual deve ser nas queries. O objectivo imediato é demonstrar que, com o simulador a correr e os dados a chegar ao Databricks, é possível responder a perguntas concretas sobre o estado da frota.

**O que está pendente:**

1. Criar os ficheiros `charging_station_simulator.py`, `electric_bus_simulator.py` e `main.py` no repositório local (os ficheiros existem mas não estavam criados na pasta do projecto)

2. Criar um notebook dedicado a queries simples no Databricks, com queries prontas para responder a perguntas como:
   - Qual o nível de bateria actual de cada autocarro?
   - Onde está cada autocarro neste momento (coordenadas GPS)?
   - Quais as estações de carregamento livres?
   - Qual autocarro tem a bateria mais baixa?
   - Algum autocarro está abaixo do nível crítico de 20%?

---

## 5. Estado Actual do Projecto

| Componente | Estado |
|---|---|
| Azure IoT Central configurado | Concluído |
| Azure Event Hub configurado | Concluído |
| Databricks - ligação ao Event Hub | Concluído |
| Databricks - tabelas Delta criadas | Concluído |
| Databricks - regras de negócio | Concluído |
| Databricks - algoritmo de decisão | Concluído |
| Simulador Python - ficheiros no repositório | Pendente |
| Databricks - notebook de queries simples | Pendente |

---

## 6. Passos Seguintes

**Passo 1 - Criar os ficheiros do simulador no repositório (próximo passo)**  
Criar os três ficheiros Python na pasta do projecto: `charging_station_simulator.py`, `electric_bus_simulator.py` e `main.py`. Verificar que as credenciais no ficheiro `.env` estão correctas. Correr o `main.py` e confirmar que os dados aparecem no Azure IoT Central.

**Passo 2 - Confirmar chegada de dados ao Databricks**  
Com o simulador a correr, abrir o Notebook 1 no Databricks e executar as células de stream. Verificar que os dados aparecem nas tabelas `bus_telemetry` e `charger_telemetry`.

**Passo 3 - Criar notebook de queries**  
Criar um novo notebook no Databricks chamado "STCP Queries" com queries SQL prontas para responder às perguntas do orientador.

**Passo 4 - Demonstração ao orientador**  
Com o simulador a correr no VS Code e o Databricks aberto, mostrar as queries a responder em tempo real.

---

## 7. Decisões Técnicas e Justificações

**Porquê Azure IoT Central e não envio directo para o Databricks?**  
O Azure IoT Central serve como camada de gestão de dispositivos. No futuro, quando os autocarros tiverem sensores reais, estes vão comunicar com o IoT Central directamente. Manter esta arquitectura agora significa que a transição do simulador para o sistema real não exige nenhuma alteração no Databricks.

**Porquê Event Hub como intermediário?**  
O Event Hub actua como buffer entre o IoT Central e o Databricks. Isto permite que o Databricks consuma os dados ao seu ritmo sem perder mensagens, mesmo que haja picos de tráfego.

**Porquê protocolo Kafka no Event Hub?**  
O Azure Event Hub é compatível com o protocolo Kafka, que é o protocolo nativo do Spark Streaming no Databricks. Esta compatibilidade elimina a necessidade de bibliotecas adicionais.

**Porquê tabelas Delta e não simples tabelas Spark?**  
As tabelas Delta permitem leituras e escritas simultâneas (stream a escrever e queries a ler ao mesmo tempo), o que é essencial para monitorização em tempo real.

**Porquê asyncio no simulador Python?**  
Os 6 dispositivos precisam de enviar telemetria em simultâneo, a cada segundo. O asyncio permite correr todas as tarefas de forma concorrente num único processo, sem criar 6 processos separados.

---

*Documento actualizado à medida que o trabalho avança. Cada secção indica o estado e a data das alterações.*