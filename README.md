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
- Qual a estação de carregamento disponível?
- Algum autocarro está abaixo do nível crítico de bateria?
- Qual autocarro tem a bateria mais baixa?
- Quais as estações com avaria?

---

## 2. Arquitectura do Sistema

O sistema funciona em camadas. Cada camada tem uma responsabilidade específica e é independente das restantes, o que significa que qualquer camada pode ser substituída sem afectar as outras.

```
[Python Simulador - VS Code] --> [Azure IoT Central] --> [Azure Event Hub] --> [Azure Databricks]
```

**Camada 1 - Simulador Python (PC Local / VS Code)**

Ficheiros: `charging_station_simulator.py`, `electric_bus_simulator.py`, `main.py`, `config.py`

Função: Gerar dados simulados de telemetria (bateria, GPS, temperatura, estado) e enviá-los para o Azure IoT Central usando o protocolo MQTT via DPS (Device Provisioning Service). Cada dispositivo liga-se de forma independente e envia telemetria a cada 5 segundos. O simulador para automaticamente ao fim de 60 segundos usando `asyncio.wait_for`.

Nota importante: No futuro, esta camada será substituída por APIs reais dos autocarros e estações de carregamento da STCP. A arquitectura das camadas seguintes não precisa de ser alterada para isso acontecer.

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

| ID | Linha | Rota | Hora de Partida | Bateria Inicial | Estado Inicial |
|---|---|---|---|---|---|
| BUS-001 | Linha 200 | Bolhão - Castelo do Queijo | 08:30 | 45% (157,5 kWh) | inTransit |
| BUS-002 | Linha 201 | Aliados - Viso | 09:00 | 70% (245 kWh) | inTransit |
| BUS-003 | Linha 202 | Aliados - Passeio Alegre | 07:45 | 25,3% (88,55 kWh) | inTransit |

Os estados e níveis de bateria iniciais foram definidos com base na folha de configuração do ficheiro Excel do projecto, que descreve um cenário realista de operação:
- BUS-001: ainda em rota, faltam 5 paragens
- BUS-002: ainda em rota, na segunda paragem
- BUS-003: a terminar a rota, bateria baixa

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

**Estados possíveis de um autocarro:**

| Estado | Descrição |
|---|---|
| parked | Estacionado no depósito |
| charging | Ligado a uma estação de carregamento |
| inTransit | Em rota activa, a consumir bateria |

### 3.2 Estações de Carregamento

Foram configuradas 3 estações de carregamento com estados distintos para simular um cenário realista de operação:

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

Quando se executa `python main.py`, o programa cria 6 instâncias de dispositivos (3 autocarros + 3 estações) e liga cada uma ao Azure IoT Central de forma independente e em paralelo usando `asyncio`. A ligação é feita via DPS, que autentica cada dispositivo pela sua chave primária.

O simulador para automaticamente ao fim de 60 segundos. Este valor pode ser alterado no parâmetro `timeout` da função `main()`.

### 4.2 Comportamento dos Autocarros

**Quando está em rota (estado inTransit):**

A bateria desce continuamente. O cálculo assume uma velocidade simulada de 5 km por segundo e um consumo de 1,2 kWh/km. As coordenadas GPS mudam ligeiramente a cada leitura com uma variação aleatória para simular movimento. A temperatura da bateria sobe gradualmente até um máximo de 35 graus Celsius.

Nota: O simulador não segue as paragens reais do GTFS. O movimento é contínuo e as coordenadas mudam de forma aproximada. A integração com os horários e paragens reais das linhas 200, 201 e 202 está prevista para uma fase posterior.

**Quando está a carregar (estado charging):**

A bateria sobe ao ritmo da potência alocada, com uma eficiência de 92%. O carregamento para automaticamente aos 95%.

**Quando está estacionado (estado parked):**

Há uma auto-descarga muito pequena que simula o consumo dos sistemas eléctricos em repouso.

### 4.3 Comportamento das Estações de Carregamento

**Estado occupied (CS-001):**

A temperatura sobe gradualmente até um máximo de 45 graus Celsius. A energia acumulada na sessão aumenta a cada leitura. A eficiência varia ligeiramente em torno dos 92%.

**Estado fault (CS-002):**

Sem potência entregue, eficiência a zero, temperatura mantém-se ligeiramente elevada (28 graus Celsius) como resultado da avaria.

**Estado available (CS-003):**

Sem potência entregue. A temperatura desce lentamente para a temperatura ambiente de 22 graus Celsius.

### 4.4 Valores Iniciais de Bateria

| Autocarro | Bateria Inicial | Estado Inicial | Descrição |
|---|---|---|---|
| BUS-001 | 45% (157,5 kWh) | inTransit | Ainda em rota, faltam 5 paragens |
| BUS-002 | 70% (245 kWh) | inTransit | Em rota, na segunda paragem |
| BUS-003 | 25,3% (88,55 kWh) | inTransit | A terminar a rota, bateria baixa |

---

## 5. Registo Cronológico do Trabalho

### Fase 1 - Configuração da Infraestrutura Azure

Criação e configuração do Azure IoT Central (plano Trial) com 6 dispositivos e dois device templates: "STCP Electric Bus" e "STCP Charging Station". Criação do Azure Event Hub (plano Student) com namespace `ehns-stcp-bus` e Event Hub `stcp-telemetry`. Configuração da regra de exportação de dados no IoT Central para enviar telemetria para o Event Hub em tempo real.

### Fase 2 - Simulador Python (Versão Inicial)

Criação dos ficheiros `charging_station_simulator.py`, `electric_bus_simulator.py` e `main.py`. Simulador com orquestrador de carregamento automático que ligava os autocarros às estações com base no nível de bateria.

### Fase 3 - Notebooks Azure Databricks

Criação de 4 notebooks no Azure Databricks Community Edition:

**Notebook 1 - STCP Dados Simulados:** Ligação ao Event Hub via Kafka, Spark Streaming, parse do JSON, tabelas Delta `bus_telemetry` e `charger_telemetry`.

**Notebook 2 - STCP Business Rules:** 8 regras de negócio como queries SQL.

**Notebook 3 - STCP Algoritmo de Decisão:** Score de urgência para cada autocarro e decisão automática de carregamento.

**Notebook 4 - STCP Simulação de Cenários:** Testes de diferentes cenários.

### Fase 4 - Simplificação por indicação do orientador

O orientador indicou que o foco actual deve ser nas queries. Os notebooks 2, 3 e 4 foram colocados em segundo plano.

### Fase 5 - Correcção da Telemetria (30 de Março de 2026)

Foram identificados e corrigidos vários problemas:

**Campo state a null:** O campo estava a ser enviado como propriedade do dispositivo em vez de telemetria. Solução: adicionado explicitamente ao dicionário de telemetria em ambos os simuladores, e adicionado aos device templates no IoT Central.

**Coordenadas GPS das estações a null:** As estações são fixas, por isso as coordenadas passaram a ser enviadas como telemetria a cada leitura em vez de propriedades do dispositivo. As coordenadas usadas correspondem ao depósito real da STCP na Rua de Bonjóia, Campanhã, Porto.

**Autocarros sempre em parked:** O orquestrador foi removido e os estados iniciais passaram a ser definidos directamente no código com base no cenário do Excel do projecto.

**Intervalo de telemetria:** Alterado de 1 segundo para 5 segundos para reduzir o volume de mensagens.

### Fase 6 - Notebook de Queries Operacionais (30 de Março de 2026)

Criação do notebook "STCP Queries" organizado em quatro grupos:

**Grupo 1 - Autocarros:**
- Estado actual de todos os autocarros
- Autocarro com a bateria mais baixa
- Autocarros em nível crítico (abaixo de 20%)
- Autonomia restante de cada autocarro (calculada como batteryKwh / 1,2)
- Vista completa de cada autocarro
- Evolução da bateria do BUS-003 nas últimas 10 leituras

**Grupo 2 - Estações de Carregamento:**
- Estado actual de todas as estações
- Estações disponíveis para carregamento
- Estações com avaria

Grupos 3 (Serviços) e 4 (Queries Combinadas) em desenvolvimento.

Todas as queries usam `ROW_NUMBER() OVER (PARTITION BY device_id ORDER BY event_time DESC)` para garantir que apenas aparece o registo mais recente de cada dispositivo, sem duplicados.

### Fase 7 - Cenário Realista nas Estações (30 de Março de 2026)

As três estações passaram a ter estados distintos para simular um cenário operacional real:
- CS-001: occupied, a carregar o BUS-004 (autocarro fictício) a 80 kW
- CS-002: fault, com avaria e fora de serviço
- CS-003: available, disponível para carregamento

Adicionado timeout de 60 segundos ao simulador usando `asyncio.wait_for`.

---

## 6. Estado Actual do Projecto

| Componente | Estado |
|---|---|
| Azure IoT Central configurado | Concluído |
| Azure Event Hub configurado | Concluído |
| Device templates actualizados | Concluído |
| Simulador Python - telemetria correcta | Concluído |
| Simulador Python - estados realistas nas estações | Concluído |
| Simulador Python - timeout de 60 segundos | Concluído |
| Databricks - tabelas Delta a receber dados | Concluído |
| Databricks - notebook de queries grupo 1 (Autocarros) | Concluído |
| Databricks - notebook de queries grupo 2 (Estações) | Concluído |
| Databricks - notebook de queries grupo 3 (Serviços) | Pendente |
| Databricks - notebook de queries grupo 4 (Combinadas) | Pendente |

---

## 7. Passos Seguintes

**Passo 1 - Grupo 3: Queries de Serviço**

Queries que respondem a perguntas operacionais mais complexas, como capacidade disponível na rede, tempo estimado para carregar um autocarro, e previsão de necessidade de carregamento.

**Passo 2 - Grupo 4: Queries Combinadas**

Queries que cruzam dados das duas tabelas, como qual a estação disponível mais próxima de um autocarro com bateria baixa.

**Passo 3 - Demonstração ao orientador**

Com o simulador a correr e o Databricks aberto, mostrar as queries a responder em tempo real.

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

Inicialmente as coordenadas eram enviadas como propriedades do dispositivo. Como as propriedades não são exportadas pelo IoT Central para o Event Hub, as coordenadas chegavam sempre a null no Databricks. A solução foi incluí-las na telemetria, mesmo sendo valores fixos.

**Porquê o simulador usa 5 km por segundo como velocidade simulada?**

Com o intervalo de telemetria de 5 segundos e o consumo de 1,2 kWh/km, uma velocidade simulada de 5 km/s produz uma descida de bateria visível entre leituras consecutivas, o que facilita a demonstração das queries em tempo real.

**Porquê o BUS-004 é fictício e não está no IoT Central?**

O BUS-004 existe apenas como valor no campo `connectedBus` da CS-001 para simular uma estação ocupada. Criar um dispositivo real no IoT Central para este efeito seria desnecessário e adicionaria complexidade sem benefício para o objectivo actual de demonstrar queries.

**Porquê o orquestrador de carregamento foi removido do main.py?**

O foco actual são as queries. O orquestrador adicionava complexidade e provocava mudanças de estado automáticas que dificultavam a demonstração. Os estados são agora definidos directamente no código com base no cenário do Excel.

**Porquê o timeout de 60 segundos?**

Permite correr o simulador por um período controlado sem necessidade de intervenção manual, útil para demonstrações e testes.

---

*Documento actualizado à medida que o trabalho avança. Última actualização: 30 de Março de 2026.*
