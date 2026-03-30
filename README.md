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

**Foco actual definido pelo orientador:** queries. Com os dados a chegar ao Databricks em tempo real, o objectivo imediato é conseguir responder a perguntas concretas sobre o estado da frota, como por exemplo:
- Qual o nível de bateria do autocarro X neste momento?
- Onde está o autocarro Y (coordenadas GPS)?
- Qual a estação de carregamento disponível?
- Algum autocarro está abaixo do nível crítico de bateria?
- Qual autocarro tem a bateria mais baixa?

---

## 2. Arquitectura do Sistema

O sistema funciona em camadas. Cada camada tem uma responsabilidade específica e é independente das restantes, o que significa que qualquer camada pode ser substituída sem afectar as outras.

```
[Python Simulador - VS Code] --> [Azure IoT Central] --> [Azure Event Hub] --> [Azure Databricks]
```

**Camada 1 - Simulador Python (PC Local / VS Code)**

Ficheiros: `charging_station_simulator.py`, `electric_bus_simulator.py`, `main.py`, `config.py`

Função: Gerar dados simulados de telemetria (bateria, GPS, temperatura, estado) e enviá-los para o Azure IoT Central usando o protocolo MQTT via DPS (Device Provisioning Service). Cada dispositivo liga-se de forma independente e envia telemetria a cada segundo.

Nota importante: No futuro, esta camada será substituída por APIs reais dos autocarros e estações de carregamento da STCP. A arquitectura das camadas seguintes não precisa de ser alterada para isso acontecer.

**Camada 2 - Azure IoT Central (Conta Trial)**

Função: Receber a telemetria de cada dispositivo, gerir a autenticação via DPS (Device Provisioning Service), e exportar os dados em tempo real para o Event Hub através de uma regra de exportação de dados configurada na plataforma. Apenas os campos definidos no device template de cada dispositivo são exportados.

**Camada 3 - Azure Event Hub (Conta Student)**

Namespace: `ehns-stcp-bus`
Nome do Event Hub: `stcp-telemetry`

Função: Actua como fila de mensagens. Recebe os dados do IoT Central e disponibiliza-os para o Databricks consumir via protocolo Kafka na porta 9093 com autenticação SASL_SSL. Garante que nenhuma mensagem se perde mesmo que o Databricks esteja temporariamente indisponível.

**Camada 4 - Azure Databricks (Community Edition)**

Função: Consome o stream de dados do Event Hub em tempo real, faz o parse do JSON recebido, separa os dados por tipo de dispositivo (autocarros vs estações de carregamento), armazena em tabelas Delta permanentes e permite fazer queries SQL sobre os dados actuais e históricos.

---

## 3. Dispositivos e Telemetria

### 3.1 Autocarros Eléctricos

Foram configurados 3 autocarros no Azure IoT Central:

| ID do Dispositivo | Linha Atribuída | Rota | Hora de Partida | Bateria Inicial | Estado Inicial |
|---|---|---|---|---|---|
| BUS-001 | Linha 200 | Bolhão - Castelo do Queijo | 08:30 | 45% (157,5 kWh) | inTransit |
| BUS-002 | Linha 201 | Aliados - Viso | 09:00 | 70% (245 kWh) | inTransit |
| BUS-003 | Linha 202 | Aliados - Passeio Alegre | 07:45 | 25% (87,5 kWh) | inTransit |

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

**Telemetria enviada por cada autocarro a cada segundo:**

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

Foram configuradas 3 estações de carregamento. As estações são fixas e não se movem, por isso as coordenadas GPS são definidas no código Python e enviadas como propriedades do dispositivo uma única vez quando o simulador arranca, e não como telemetria a cada segundo.

A localização é o depósito da STCP na Rua de Bonjóia, Campanhã, Porto (coordenadas reais obtidas a partir da morada oficial da STCP).

| ID | Latitude | Longitude | Potência Máxima |
|---|---|---|---|
| CS-001 | 41.152661 | -8.579658 | 120 kW |
| CS-002 | 41.152671 | -8.579668 | 120 kW |
| CS-003 | 41.152681 | -8.579678 | 120 kW |

**Limite total da rede eléctrica:** 300 kW (soma das três estações em simultâneo)

**Telemetria enviada por cada estação a cada segundo:**

| Campo | Tipo | Descrição |
|---|---|---|
| state | Texto | available (livre) ou occupied (ocupada) |
| currentPower | Double (kW) | Potência a ser entregue neste momento |
| currentEfficiency | Double (%) | Eficiência actual do carregamento |
| chargerTemperature | Double (Celsius) | Temperatura do equipamento |
| energyDelivered | Double (kWh) | Energia entregue na sessão actual |
| connectedBus | Texto | ID do autocarro ligado (null se livre) |

---

## 4. O que o Simulador está a Fazer

### 4.1 Arranque

Quando se executa `python main.py`, o programa cria 6 instâncias de dispositivos (3 autocarros + 3 estações) e liga cada uma ao Azure IoT Central de forma independente e em paralelo, usando a biblioteca `asyncio` do Python. A ligação é feita via DPS (Device Provisioning Service), que autentica cada dispositivo pela sua chave primária e atribui o IoT Hub correcto.

Após a ligação, cada dispositivo começa imediatamente a enviar telemetria a cada segundo.

### 4.2 Comportamento dos Autocarros

**Quando está em rota (estado inTransit):**

A bateria desce continuamente. O cálculo assume uma velocidade média constante de 50 km/h e um consumo de 1,2 kWh/km. A cada segundo, o autocarro percorre aproximadamente 0,014 km e consome a energia correspondente. As coordenadas GPS mudam ligeiramente a cada segundo com uma variação aleatória pequena para simular movimento. A temperatura da bateria sobe gradualmente até um máximo de 35 graus Celsius.

Nota: O simulador não segue as paragens reais do GTFS. O movimento é contínuo e as coordenadas mudam de forma aproximada. A integração com os horários e paragens reais das linhas 200, 201 e 202 está prevista para uma fase posterior.

**Quando está a carregar (estado charging):**

A bateria sobe ao ritmo da potência alocada, com uma eficiência de 92%. O carregamento para automaticamente aos 95% para proteger a bateria. A temperatura da bateria sobe gradualmente até um máximo de 40 graus Celsius.

**Quando está estacionado (estado parked):**

Há uma auto-descarga muito pequena que simula o consumo dos sistemas eléctricos do autocarro em repouso. A temperatura desce lentamente para a temperatura ambiente.

### 4.3 Comportamento das Estações de Carregamento

**Quando está livre (estado available):**

A potência entregue é zero. A temperatura do equipamento desce lentamente para a temperatura ambiente de 22 graus Celsius.

**Quando está ocupada (estado occupied):**

A temperatura do equipamento sobe gradualmente até um máximo de 45 graus Celsius. A energia acumulada na sessão aumenta a cada segundo. A eficiência varia ligeiramente em torno dos 92%.

### 4.4 Valores Iniciais de Bateria

| Autocarro | Bateria Inicial | Estado Inicial | Descrição |
|---|---|---|---|
| BUS-001 | 45% (157,5 kWh) | inTransit | Ainda em rota, faltam 5 paragens |
| BUS-002 | 70% (245 kWh) | inTransit | Em rota, na segunda paragem |
| BUS-003 | 25% (87,5 kWh) | inTransit | A terminar a rota, bateria baixa |

---

## 5. Registo Cronológico do Trabalho

### Fase 1 - Configuração da Infraestrutura Azure

Foi criada a conta Azure IoT Central (plano Trial) e configurados os 6 dispositivos. Para cada dispositivo foi gerada uma chave primária de autenticação. Foram criados dois device templates: "STCP Electric Bus" para os autocarros e "STCP Charging Station" para as estações.

Foi criada a conta Azure (plano Student) para o Event Hub. Foi criado um namespace chamado `ehns-stcp-bus` e dentro dele um Event Hub chamado `stcp-telemetry`. Foi configurada uma política de acesso `RootManageSharedAccessKey`.

No Azure IoT Central foi configurada uma regra de exportação de dados que envia toda a telemetria recebida para o Event Hub em tempo real, no formato JSON.

As credenciais estão guardadas no ficheiro `.env` que não está no repositório por conter informação privada. Está listado no `.gitignore`.

### Fase 2 - Simulador Python (Versão Inicial)

Foram criados três ficheiros Python: `charging_station_simulator.py`, `electric_bus_simulator.py` e `main.py`. O simulador ligava os dispositivos ao Azure IoT Central e enviava telemetria a cada segundo. O `main.py` incluía um orquestrador de carregamento automático que ligava os autocarros às estações com base no nível de bateria.

### Fase 3 - Notebooks Azure Databricks

Foram criados 4 notebooks no Azure Databricks Community Edition:

**Notebook 1 - STCP Dados Simulados:** Configura a ligação ao Event Hub via Kafka, cria um Spark Streaming DataFrame que lê os dados em tempo real, faz o parse do JSON, separa os dados por tipo de dispositivo e escreve nas tabelas Delta `bus_telemetry` e `charger_telemetry`.

**Notebook 2 - STCP Business Rules:** Implementa 8 regras de negócio como queries SQL sobre as tabelas Delta.

**Notebook 3 - STCP Algoritmo de Decisão:** Algoritmo que combina as 8 regras para calcular um score de urgência para cada autocarro e decidir automaticamente qual carregar, em qual estação e com que potência.

**Notebook 4 - STCP Simulação de Cenários:** Permite testar diferentes cenários manualmente.

### Fase 4 - Simplificação por indicação do orientador

O orientador indicou que o foco actual deve ser nas queries. Os notebooks 2, 3 e 4 foram colocados em segundo plano. O objectivo imediato é demonstrar que, com o simulador a correr e os dados a chegar ao Databricks, é possível responder a perguntas concretas sobre o estado da frota em tempo real.

### Fase 5 - Correcção da Telemetria (30 de Março de 2026)

Foram identificados e corrigidos vários problemas na telemetria:

**Problema 1 - Campo state a null:**

O campo `state` estava a ser enviado como propriedade do dispositivo (device twin) em vez de telemetria. O Azure IoT Central trata estes dois conceitos de forma distinta: as propriedades descrevem o dispositivo e não são exportadas para o Event Hub pela regra de exportação de dados. Apenas a telemetria é exportada.

Solução: o campo `state` foi adicionado explicitamente ao dicionário de telemetria em ambos os simuladores. Foi também necessário adicionar `state` e `connectedBus` como campos de telemetria nos device templates do Azure IoT Central, caso contrário o IoT Central ignora os campos que não estão definidos no template durante a exportação.

**Problema 2 - Coordenadas GPS das estações a null:**

As estações de carregamento não enviavam coordenadas GPS. Como as estações são fixas e nunca mudam de posição, a solução foi definir as coordenadas directamente no código Python e enviá-las como propriedades do dispositivo no arranque, em vez de as enviar como telemetria a cada segundo.

As coordenadas usadas são as coordenadas reais do depósito da STCP na Rua de Bonjóia, Campanhã, Porto (latitude: 41.152661, longitude: -8.579658), obtidas a partir da morada oficial publicada pela STCP.

**Problema 3 - Autocarros sempre em estado parked:**

O orquestrador de carregamento automático foi removido do `main.py` para simplificar. Sem ele, os autocarros ficavam sempre em estado `parked` e nunca mudavam de estado.

Solução: os estados e níveis de bateria iniciais de cada autocarro foram definidos directamente no código com base no cenário definido na folha de configuração do Excel do projecto. Os três autocarros arrancam agora em estado `inTransit` com os níveis de bateria correctos, e a bateria desce gradualmente enquanto o simulador corre.

**Problema 4 - Código antigo ainda a ser executado:**

Durante a correcção do campo `state`, verificou-se que o JSON enviado ao Event Hub ainda continha os campos antigos. Após investigação, confirmou-se que o Azure IoT Central estava a filtrar o campo `state` por não estar definido no device template. A solução foi adicionar o campo ao template e manter os campos existentes no payload de telemetria para compatibilidade.

---

## 6. Estado Actual do Projecto

| Componente | Estado |
|---|---|
| Azure IoT Central configurado | Concluído |
| Azure Event Hub configurado | Concluído |
| Device templates actualizados com campo state | Concluído |
| Simulador Python - telemetria correcta com state | Concluído |
| Simulador Python - coordenadas GPS reais das estações | Concluído |
| Simulador Python - estados iniciais dos autocarros correctos | Concluído |
| Databricks - ligação ao Event Hub | Concluído |
| Databricks - tabelas Delta criadas | Concluído |
| Databricks - campo state a aparecer correctamente | Concluído |
| Databricks - notebook de queries simples | Pendente |

---

## 7. Passos Seguintes

**Passo 1 - Criar notebook de queries no Databricks**

Criar um novo notebook no Databricks com queries SQL prontas para responder às perguntas do orientador sobre o estado actual da frota em tempo real.

Queries previstas:
- Nível de bateria actual de cada autocarro
- Localização GPS actual de cada autocarro
- Estado de cada estação de carregamento (livre ou ocupada)
- Autocarro com a bateria mais baixa
- Autocarros abaixo do nível crítico de 20%
- Estações disponíveis para carregamento

**Passo 2 - Demonstração ao orientador**

Com o simulador a correr no VS Code e o Databricks aberto, mostrar as queries a responder em tempo real, com os valores da bateria a mudar a cada vez que a query é executada.

---

## 8. Decisões Técnicas e Justificações

**Porquê Azure IoT Central e não envio directo para o Databricks?**

O Azure IoT Central serve como camada de gestão de dispositivos. No futuro, quando os autocarros tiverem sensores reais, estes vão comunicar com o IoT Central directamente. Manter esta arquitectura agora significa que a transição do simulador para o sistema real não exige nenhuma alteração no Databricks.

**Porquê Event Hub como intermediário?**

O Event Hub actua como buffer entre o IoT Central e o Databricks. Permite que o Databricks consuma os dados ao seu ritmo sem perder mensagens, mesmo que haja picos de tráfego ou interrupções temporárias.

**Porquê protocolo Kafka no Event Hub?**

O Azure Event Hub é compatível com o protocolo Kafka, que é o protocolo nativo do Spark Streaming no Databricks. Esta compatibilidade elimina a necessidade de bibliotecas adicionais.

**Porquê tabelas Delta e não simples tabelas Spark?**

As tabelas Delta permitem leituras e escritas simultâneas, o que é essencial para monitorização em tempo real: o stream escreve continuamente enquanto as queries lêem os dados mais recentes.

**Porquê asyncio no simulador Python?**

Os 6 dispositivos precisam de enviar telemetria em simultâneo, a cada segundo. O asyncio permite correr todas as tarefas de forma concorrente num único processo, sem criar 6 processos separados.

**Porquê as coordenadas GPS das estações são propriedades e não telemetria?**

As estações de carregamento são fixas e nunca mudam de localização. Enviar coordenadas GPS a cada segundo como telemetria seria redundante. As coordenadas são enviadas uma única vez como propriedades do dispositivo quando o simulador arranca.

**Porquê o simulador não segue as paragens reais do GTFS nesta fase?**

A integração com os horários e coordenadas reais das linhas 200, 201 e 202 adiciona complexidade que não é necessária para o objectivo actual de demonstrar queries. O movimento contínuo com descarga proporcional à distância é suficiente para mostrar que a bateria desce enquanto o autocarro está em rota. A integração GTFS está prevista para uma fase posterior.

**Porquê o orquestrador de carregamento foi removido do main.py?**

O foco actual do projecto são as queries. O orquestrador adicionava complexidade e provocava mudanças de estado automáticas que dificultavam a demonstração dos dados. Os estados iniciais dos autocarros são agora definidos directamente no código com base no cenário do Excel, o que torna a simulação mais previsível e controlada para fins de demonstração.

---

*Documento actualizado à medida que o trabalho avança. Última actualização: 30 de Março de 2026.*