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
4. O que o Simulador está a Fazer
5. Registo Cronológico do Trabalho
6. Estado Actual do Projecto
7. Passos Seguintes
8. Decisões Técnicas e Justificações

---

## 1. Contexto e Objectivo do Projecto

O projecto tem como objectivo simular e monitorizar em tempo real o sistema de carregamento de autocarros eléctricos da STCP (Sociedade de Transportes Colectivos do Porto). O sistema permite acompanhar o estado da frota - nível de bateria, localização GPS, estado das estações de carregamento - através de dados de telemetria enviados para a nuvem.

A arquitectura foi desenhada para simular, na fase académica, o que em produção seria feito por APIs e sensores reais instalados nos autocarros e nas estações de carregamento. Isto significa que o simulador Python é apenas temporário e substituível, sem necessidade de alterar o resto da arquitectura.

**Foco actual definido pelo orientador:** queries. Com os dados a chegar ao Databricks em tempo real, o objectivo é conseguir responder a perguntas concretas sobre o estado da frota, como por exemplo:
- Qual o nível de bateria do autocarro X neste momento?
- Onde está o autocarro Y (coordenadas GPS)?
- Em que paragem está o autocarro Z?
- Quantas paragens faltam para o autocarro terminar a rota?
- Qual a estação de carregamento disponível?
- Algum autocarro está abaixo do nível crítico de bateria?
- Há estações suficientes para todos os autocarros que precisam de carregar?

---

## 2. Arquitectura do Sistema

O sistema funciona em camadas. Cada camada tem uma responsabilidade específica e é independente das restantes, o que significa que qualquer camada pode ser substituída sem afectar as outras.

```
[Python Simulador - VS Code] --> [Azure IoT Central] --> [Azure Event Hub] --> [Azure Databricks]
```

**Camada 1 - Simulador Python (PC Local / VS Code)**

Ficheiros: `charging_station_simulator.py`, `electric_bus_simulator.py`, `main.py`, `config.py`

Função: Gerar dados simulados de telemetria e enviá-los para o Azure IoT Central usando o protocolo MQTT via DPS. Cada dispositivo liga-se de forma independente e envia telemetria a cada 5 segundos. O simulador para automaticamente ao fim de 60 segundos usando `asyncio.wait_for`.

Nota importante: No futuro, esta camada será substituída por APIs reais dos autocarros e estações de carregamento da STCP. A arquitectura das camadas seguintes não precisa de ser alterada.

**Camada 2 - Azure IoT Central (Conta Trial)**

Função: Receber a telemetria de cada dispositivo, gerir a autenticação via DPS, e exportar os dados em tempo real para o Event Hub. Apenas os campos definidos no device template de cada dispositivo são exportados.

**Camada 3 - Azure Event Hub (Conta Student)**

Namespace: `ehns-stcp-bus`
Nome do Event Hub: `stcp-telemetry`

Função: Actua como fila de mensagens entre o IoT Central e o Databricks. Garante que nenhuma mensagem se perde mesmo que o Databricks esteja temporariamente indisponível.

**Camada 4 - Azure Databricks (Community Edition)**

Função: Consome o stream de dados do Event Hub em tempo real, faz o parse do JSON, separa os dados por tipo de dispositivo, armazena em tabelas Delta permanentes e permite fazer queries SQL sobre os dados actuais e históricos.

---

## 3. Dispositivos e Telemetria

### 3.1 Autocarros Eléctricos

Foram configurados 3 autocarros no Azure IoT Central:

| ID | Linha | Rota | Hora de Partida | Bateria Inicial | Estado Inicial | Distância Inicial (m) |
|---|---|---|---|---|---|---|
| BUS-001 | Linha 200 | Bolhão - Castelo do Queijo | 08:30 | 45% (157,5 kWh) | inTransit | 8098,83 |
| BUS-002 | Linha 201 | Aliados - Viso | 09:00 | 70% (245 kWh) | inTransit | 696,96 |
| BUS-003 | Linha 202 | Aliados - Passeio Alegre | 07:45 | 25,3% (88,55 kWh) | inTransit | 5313,20 |

Os estados, níveis de bateria e distâncias iniciais foram definidos com base na folha de configuração do ficheiro Excel do projecto:
- BUS-001: faltam 5 paragens de 30, está na paragem 25 (8098,83 metros percorridos)
- BUS-002: está na segunda paragem (696,96 metros percorridos)
- BUS-003: a terminar a rota, perto da última paragem (5313,20 metros percorridos)

**Especificações técnicas (baseadas no CaetanoBus e.City Gold):**

| Parâmetro | Valor |
|---|---|
| Capacidade da bateria | 350 kWh |
| Consumo médio | 1,2 kWh/km |
| Nível mínimo de segurança | 20% |
| Nível máximo de carregamento | 95% |
| Faixa operacional ideal | 20% a 80% |

**Telemetria enviada por cada autocarro a cada 5 segundos:**

| Campo | Tipo | Descrição |
|---|---|---|
| batteryLevel | Double (%) | Estado de carga da bateria |
| batteryKwh | Double (kWh) | Energia disponível na bateria |
| batteryTemperature | Double (Celsius) | Temperatura da bateria |
| latitude | Double | Coordenada GPS actual |
| longitude | Double | Coordenada GPS actual |
| instantConsumption | Double (kW) | Consumo instantâneo de energia |
| remainingRange | Double (km) | Autonomia restante estimada |
| state | Texto | Estado operacional actual |
| distanceTraveled | Double (metros) | Distância percorrida na rota actual |

**Estados possíveis de um autocarro:**

| Estado | Descrição |
|---|---|
| parked | Estacionado no depósito |
| charging | Ligado a uma estação de carregamento |
| inTransit | Em rota activa, a consumir bateria |

### 3.2 Estações de Carregamento

Foram configuradas 3 estações com estados distintos para simular um cenário realista:

| ID | Estado Inicial | Descrição | Latitude | Longitude |
|---|---|---|---|---|
| CS-001 | occupied | A carregar o BUS-004 (autocarro fictício) a 80 kW | 41.152661 | -8.579658 |
| CS-002 | fault | Com avaria, fora de serviço | 41.152671 | -8.579668 |
| CS-003 | available | Disponível para carregamento | 41.152681 | -8.579678 |

A localização corresponde ao depósito da STCP na Rua de Bonjóia, Campanhã, Porto.

O BUS-004 é um autocarro fictício usado apenas para simular uma estação ocupada. Não existe como dispositivo no Azure IoT Central.

**Limite total da rede eléctrica:** 300 kW (soma das três estações em simultâneo)

**Telemetria enviada por cada estação a cada 5 segundos:**

| Campo | Tipo | Descrição |
|---|---|---|
| state | Texto | available, occupied ou fault |
| currentPower | Double (kW) | Potência a ser entregue neste momento |
| currentEfficiency | Double (%) | Eficiência actual do carregamento |
| chargerTemperature | Double (Celsius) | Temperatura do equipamento |
| energyDelivered | Double (kWh) | Energia entregue na sessão actual |
| connectedBus | Texto | ID do autocarro ligado (null se livre) |
| latitude | Double | Coordenada GPS da estação |
| longitude | Double | Coordenada GPS da estação |

**Estados possíveis de uma estação:**

| Estado | Descrição |
|---|---|
| available | Livre, pronta para receber um autocarro |
| occupied | A carregar um autocarro activamente |
| fault | Com avaria, fora de serviço |

---

## 4. O que o Simulador está a Fazer

### 4.1 Arranque

Quando se executa `python main.py`, o programa cria 6 instâncias de dispositivos e liga cada uma ao Azure IoT Central em paralelo usando `asyncio`. O simulador para automaticamente ao fim de 60 segundos.

### 4.2 Comportamento dos Autocarros

**Quando está em rota (estado inTransit):**

A bateria desce continuamente com base na distância percorrida. O campo `distanceTraveled` aumenta 50 metros por segundo (0,05 km/s). A cada segundo, o autocarro consome energia proporcional à distância percorrida com base no consumo médio de 1,2 kWh/km. As coordenadas GPS mudam ligeiramente a cada leitura. A temperatura da bateria sobe gradualmente até um máximo de 35 graus Celsius.

Nota: O GPS é aproximado e não segue as coordenadas exactas das paragens GTFS. A paragem actual é determinada pelo campo `distanceTraveled` em comparação com a tabela `route_stops` no Databricks.

**Quando está a carregar (estado charging):**

A bateria sobe ao ritmo da potência alocada com eficiência de 92%. Para automaticamente aos 95%.

**Quando está estacionado (estado parked):**

Auto-descarga muito pequena que simula o consumo dos sistemas em repouso.

### 4.3 Comportamento das Estações

**Estado occupied (CS-001):** Temperatura sobe até máximo de 45 graus Celsius, energia acumula, eficiência varia em torno dos 92%.

**Estado fault (CS-002):** Sem potência, eficiência a zero, temperatura mantém-se ligeiramente elevada.

**Estado available (CS-003):** Sem potência, temperatura desce para 22 graus Celsius.

### 4.4 Tabela de Referência das Paragens

Foi criada no Databricks uma tabela Delta estática chamada `route_stops` com os horários e coordenadas reais das paragens das três linhas, obtidos dos dados GTFS da STCP:

- Linha 200 (BUS-001): 30 paragens, Bolhão até Castelo do Queijo, 9853,9 metros
- Linha 201 (BUS-002): 26 paragens, Aliados até Viso, 9777,63 metros
- Linha 202 (BUS-003): 16 paragens, S. João de Brito até Passeio Alegre, 5313,2 metros

Esta tabela permite cruzar a distância percorrida em tempo real com as paragens reais para determinar onde cada autocarro está na rota.

---

## 5. Registo Cronológico do Trabalho

### Fase 1 - Configuração da Infraestrutura Azure

Criação do Azure IoT Central (plano Trial) com 6 dispositivos e dois device templates: "STCP Electric Bus" e "STCP Charging Station". Criação do Azure Event Hub (plano Student) com namespace `ehns-stcp-bus` e Event Hub `stcp-telemetry`. Configuração da regra de exportação de dados no IoT Central.

### Fase 2 - Simulador Python (Versão Inicial)

Criação dos ficheiros `charging_station_simulator.py`, `electric_bus_simulator.py` e `main.py` com orquestrador de carregamento automático.

### Fase 3 - Notebooks Azure Databricks

Criação de 4 notebooks: STCP Dados Simulados, STCP Business Rules, STCP Algoritmo de Decisão e STCP Simulação de Cenários.

### Fase 4 - Simplificação por indicação do orientador

Foco reduzido às queries. Notebooks 2, 3 e 4 colocados em segundo plano.

### Fase 5 - Correcção da Telemetria (30 de Março de 2026)

Correcção de vários problemas: campo `state` a null (estava como propriedade em vez de telemetria), coordenadas GPS das estações a null (passaram para telemetria), autocarros sempre em `parked` (estados iniciais definidos no código com base no Excel), intervalo de telemetria alterado de 1 para 5 segundos.

### Fase 6 - Notebook de Queries Operacionais (30 de Março de 2026)

Criação do notebook "STCP Queries" organizado em quatro grupos:

**Grupo 1 - Autocarros:**
- Estado actual de todos os autocarros
- Autocarro com a bateria mais baixa
- Autocarros em nível crítico (abaixo de 20%)
- Autonomia restante de cada autocarro
- Vista completa de cada autocarro
- Evolução da bateria do BUS-003

**Grupo 2 - Estações de Carregamento:**
- Estado actual de todas as estações
- Estações disponíveis para carregamento
- Estações com avaria

**Grupo 3 - Serviços:**
- Capacidade disponível na rede de carregamento
- Tempo estimado para carregar cada autocarro até 80%
- Autocarros que precisam de carregar antes da próxima rota
- Paragem mais próxima de cada autocarro (baseado em distanceTraveled)
- Quantas paragens faltam para cada autocarro terminar a rota

**Grupo 4 - Queries Combinadas:**
- Qual o autocarro que está a ser carregado em cada estação
- Há estações suficientes para os autocarros que precisam de carregar?
- Custo estimado para carregar todos os autocarros até 80%

Todas as queries usam `ROW_NUMBER() OVER (PARTITION BY device_id ORDER BY event_time DESC)` para garantir que apenas aparece o registo mais recente de cada dispositivo.

### Fase 7 - Cenário Realista nas Estações (30 de Março de 2026)

Estados distintos nas estações: CS-001 occupied (a carregar BUS-004 fictício), CS-002 fault (avaria), CS-003 available. Adicionado timeout de 60 segundos ao simulador.

### Fase 8 - Campo distanceTraveled e Tabela de Paragens (30 de Março de 2026)

Adicionado o campo `distanceTraveled` à telemetria dos autocarros para rastrear a posição na rota com precisão. Os valores iniciais de distância foram definidos com base no estado descrito no Excel do projecto.

Criada a tabela Delta estática `route_stops` no Databricks com os dados reais GTFS das três linhas (72 paragens no total). Esta tabela permite determinar em que paragem está cada autocarro e quantas paragens faltam para terminar a rota, cruzando o `distanceTraveled` em tempo real com as distâncias reais das paragens.

---

## 6. Estado Actual do Projecto

| Componente | Estado |
|---|---|
| Azure IoT Central configurado | Concluído |
| Azure Event Hub configurado | Concluído |
| Device templates actualizados | Concluído |
| Simulador Python - telemetria completa | Concluído |
| Simulador Python - campo distanceTraveled | Concluído |
| Simulador Python - estados realistas nas estações | Concluído |
| Simulador Python - timeout de 60 segundos | Concluído |
| Databricks - tabelas Delta a receber dados | Concluído |
| Databricks - tabela route_stops com dados GTFS | Concluído |
| Databricks - notebook de queries grupo 1 (Autocarros) | Concluído |
| Databricks - notebook de queries grupo 2 (Estações) | Concluído |
| Databricks - notebook de queries grupo 3 (Serviços) | Concluído |
| Databricks - notebook de queries grupo 4 (Combinadas) | Concluído |

---

## 7. Passos Seguintes

**Passo 1 - Demonstração ao orientador**

Com o simulador a correr no VS Code e o Databricks aberto, mostrar as queries dos 4 grupos a responder em tempo real.

**Passo 2 - Melhorias futuras**

- Integração GPS real com as coordenadas das paragens GTFS (mover o autocarro de paragem em paragem em vez de movimento aleatório)
- Substituição do simulador Python por APIs reais dos autocarros e estações da STCP

---

## 8. Decisões Técnicas e Justificações

**Porquê Azure IoT Central e não envio directo para o Databricks?**

O Azure IoT Central serve como camada de gestão de dispositivos. No futuro, quando os autocarros tiverem sensores reais, estes vão comunicar com o IoT Central directamente. Manter esta arquitectura agora significa que a transição do simulador para o sistema real não exige nenhuma alteração no Databricks.

**Porquê Event Hub como intermediário?**

O Event Hub actua como buffer entre o IoT Central e o Databricks. Permite que o Databricks consuma os dados ao seu ritmo sem perder mensagens.

**Porquê protocolo Kafka no Event Hub?**

O Azure Event Hub é compatível com o protocolo Kafka, que é o protocolo nativo do Spark Streaming no Databricks. Esta compatibilidade elimina a necessidade de bibliotecas adicionais.

**Porquê tabelas Delta e não simples tabelas Spark?**

As tabelas Delta permitem leituras e escritas simultâneas, essencial para monitorização em tempo real.

**Porquê asyncio no simulador Python?**

Os 6 dispositivos precisam de enviar telemetria em simultâneo. O asyncio permite correr todas as tarefas de forma concorrente num único processo.

**Porquê as coordenadas das estações são enviadas como telemetria e não como propriedades?**

As propriedades do dispositivo não são exportadas pelo IoT Central para o Event Hub, por isso chegavam sempre a null no Databricks. A solução foi incluí-las na telemetria.

**Porquê o campo distanceTraveled em vez de usar apenas o GPS?**

O GPS simulado é aproximado e não coincide com as coordenadas reais das paragens. O campo `distanceTraveled` acumula a distância percorrida desde o início da rota e permite determinar com precisão em que paragem está o autocarro, cruzando com as distâncias reais das paragens na tabela `route_stops`.

**Porquê a tabela route_stops é estática no Databricks e não vem do IoT Central?**

Os horários e paragens são dados de referência fixos que nunca mudam. O Azure IoT Central é para telemetria de dispositivos em tempo real. Guardar dados estáticos no Databricks é a abordagem correcta e permite fazer JOINs eficientes com os dados em tempo real.

**Porquê o BUS-004 é fictício?**

O BUS-004 existe apenas como valor no campo `connectedBus` da CS-001 para simular uma estação ocupada. Criar um dispositivo real no IoT Central seria desnecessário para o objectivo actual de demonstrar queries.

**Porquê o timeout de 60 segundos?**

Permite correr o simulador por um período controlado sem necessidade de intervenção manual, útil para demonstrações.

**Porquê o orquestrador de carregamento foi removido?**

O foco actual são as queries. O orquestrador adicionava complexidade e provocava mudanças de estado automáticas que dificultavam a demonstração. Os estados são definidos directamente no código com base no cenário do Excel.

---

*Documento actualizado à medida que o trabalho avança. Última actualização: 30 de Março de 2026.*