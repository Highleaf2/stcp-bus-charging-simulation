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

Ficheiros: `charging_station_simulator.py`, `electric_bus_simulator.py`, `main.py`

Função: Gerar dados simulados de telemetria (bateria, GPS, temperatura, estado) e enviá-los para o Azure IoT Central usando o protocolo MQTT via DPS (Device Provisioning Service). Cada dispositivo liga-se de forma independente e envia telemetria a cada segundo.

Nota importante: No futuro, esta camada será substituída por APIs reais dos autocarros e estações de carregamento da STCP. A arquitectura das camadas seguintes não precisa de ser alterada para isso acontecer.

**Camada 2 - Azure IoT Central (Conta Trial)**

Função: Receber a telemetria de cada dispositivo, gerir a autenticação via DPS (Device Provisioning Service), e exportar os dados em tempo real para o Event Hub através de uma regra de exportação de dados configurada na plataforma.

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

| ID do Dispositivo | Linha Atribuída | Rota | Hora de Partida | Bateria Inicial |
|---|---|---|---|---|
| BUS-001 | Linha 200 | Bolhão - Castelo do Queijo | 08:30 | 45% (157,5 kWh) |
| BUS-002 | Linha 201 | Aliados - Viso | 09:00 | 70% (245 kWh) |
| BUS-003 | Linha 202 | Aliados - Passeio Alegre | 07:45 | 25% (87,5 kWh) |

**Especificações técnicas (baseadas no CaetanoBus e.City Gold):**

| Parâmetro | Valor | Fonte |
|---|---|---|
| Capacidade da bateria | 350 kWh | Valores de referência de mercado |
| Consumo médio | 1,2 kWh/km | Uso urbano típico |
| Nível mínimo de segurança | 20% | Não descarregar abaixo deste valor |
| Nível máximo de carregamento | 95% | Protecção da bateria |
| Faixa operacional ideal | 20% a 80% | Preservação da vida útil |

**Telemetria enviada por cada autocarro a cada segundo:**

| Campo | Tipo | Descrição |
|---|---|---|
| batteryLevel | Percentagem (%) | Estado de carga da bateria |
| batteryKwh | Double (kWh) | Energia disponível na bateria |
| batteryTemperature | Double (Celsius) | Temperatura da bateria |
| latitude | Double | Coordenada GPS actual |
| longitude | Double | Coordenada GPS actual |
| state | Texto | Estado operacional actual |

**Estados possíveis de um autocarro:**

| Estado | Descrição |
|---|---|
| PARKED | Estacionado no depósito, sistemas desligados |
| CHARGING | Ligado a uma estação de carregamento, a receber energia |
| ROUTE | Em rota activa, a consumir bateria |
| IDLE_ON_ROUTE | Parado em sinal ou paragem intermédia |

### 3.2 Estações de Carregamento

Foram configuradas 3 estações de carregamento:

| ID do Dispositivo | Potência Máxima | Eficiência | Custo |
|---|---|---|---|
| CS-001 | 120 kW | 92% | 0,15 €/kWh |
| CS-002 | 120 kW | 92% | 0,15 €/kWh |
| CS-003 | 120 kW | 92% | 0,15 €/kWh |

**Limite total da rede eléctrica:** 300 kW (soma das três estações em simultâneo)

**Tarifas eléctricas simuladas:**

| Período | Tarifa |
|---|---|
| Vazio nocturno (23h-7h) | 0,10 €/kWh |
| Tarifa base | 0,15 €/kWh |
| Ponta (9h-12h e 18h-21h) | 0,22 €/kWh |

**Telemetria enviada por cada estação a cada segundo:**

| Campo | Tipo | Descrição |
|---|---|---|
| state | Texto | IDLE (livre) ou CHARGING (ocupada) |
| currentPower | Double (kW) | Potência a ser entregue neste momento |
| currentEfficiency | Double (%) | Eficiência actual do carregamento |
| chargerTemperature | Double (Celsius) | Temperatura do equipamento |
| energyDelivered | Double (kWh) | Energia entregue na sessão actual |
| totalEnergyDelivered | Double (kWh) | Energia total entregue desde o início |
| connectedBus | Texto | ID do autocarro ligado (null se livre) |

---

## 4. O que o Simulador está a Fazer

Esta secção descreve com rigor o que acontece quando o `main.py` é executado, para que seja claro o que os dados representam e quais as suas limitações actuais.

### 4.1 Arranque

Quando se executa `python main.py`, o programa cria 6 instâncias de dispositivos (3 autocarros + 3 estações) e liga cada uma ao Azure IoT Central de forma independente e em paralelo, usando a biblioteca `asyncio` do Python. A ligação é feita via DPS (Device Provisioning Service), que autentica cada dispositivo pela sua chave primária e atribui o IoT Hub correcto.

Após a ligação, cada dispositivo começa imediatamente a enviar telemetria a cada segundo.

### 4.2 Comportamento dos Autocarros

**Quando está em rota (estado ROUTE):**

A bateria desce continuamente. O cálculo assume uma velocidade média constante de 50 km/h e um consumo de 1,2 kWh/km. A cada segundo, o autocarro "percorre" aproximadamente 0,014 km e consome a energia correspondente. As coordenadas GPS mudam ligeiramente a cada segundo com uma variação aleatória pequena para simular movimento. A temperatura da bateria sobe gradualmente até um máximo de 35°C.

Nota importante: O simulador actual não segue as paragens reais do GTFS. O movimento é contínuo e as coordenadas mudam de forma aproximada, não paragem a paragem. A integração com os horários e paragens reais das linhas 200, 201 e 202 está prevista para uma fase posterior.

**Quando está a carregar (estado CHARGING):**

A bateria sobe ao ritmo da potência alocada (80 kW), com uma eficiência de 92%. O carregamento para automaticamente aos 95% para proteger a bateria. A temperatura da bateria sobe gradualmente até um máximo de 40°C durante o carregamento.

**Quando está estacionado (estado PARKED):**

Há uma auto-descarga muito pequena (0,0001 kWh por segundo) que simula o consumo dos sistemas eléctricos do autocarro em repouso. A temperatura desce lentamente para a temperatura ambiente (20°C).

### 4.3 Comportamento das Estações de Carregamento

**Quando está livre (estado IDLE):**

A potência entregue é zero. A temperatura do equipamento desce lentamente para a temperatura ambiente (22°C).

**Quando está a carregar (estado CHARGING):**

A temperatura do equipamento sobe gradualmente até um máximo de 45°C. A energia acumulada na sessão aumenta a cada segundo. A eficiência varia ligeiramente em torno dos 92%.

### 4.4 Lógica de Carregamento Automático

O orquestrador (`simple_charging_orchestrator` no `main.py`) verifica o estado de todos os autocarros a cada 5 segundos e aplica duas regras simples:

Regra 1: Se a bateria de um autocarro estiver abaixo de 50% e o autocarro estiver estacionado, o orquestrador procura a primeira estação disponível e liga o autocarro a ela, alocando 80 kW de potência.

Regra 2: Se a bateria de um autocarro em carregamento atingir 90% ou mais, o orquestrador desliga o carregamento e o autocarro volta ao estado estacionado.

Esta é uma lógica básica intencional. O algoritmo de optimização completo (que considera prioridade de rotas, tempo até à partida, balanceamento de carga e temperatura) está implementado no Notebook 3 do Databricks e será integrado numa fase posterior.

### 4.5 Valores Iniciais de Bateria e Implicações

| Autocarro | Bateria Inicial | Situação |
|---|---|---|
| BUS-001 | 45% (157,5 kWh) | Abaixo de 50%, será ligado a carregar imediatamente |
| BUS-002 | 70% (245 kWh) | Acima de 50%, permanece estacionado até descer |
| BUS-003 | 25% (87,5 kWh) | Abaixo de 50% e abaixo do nível crítico de 20%, prioridade máxima |

Quando o simulador arranca, o BUS-001 e o BUS-003 devem ser ligados automaticamente a estações de carregamento dentro dos primeiros 10 a 15 segundos.

---

## 5. Registo Cronológico do Trabalho

### Fase 1 - Configuração da Infraestrutura Azure

Foi criada a conta Azure IoT Central (plano Trial) e configurados os 6 dispositivos. Para cada dispositivo foi gerada uma chave primária de autenticação.

Foi criada a conta Azure (plano Student) para o Event Hub. Foi criado um namespace chamado `ehns-stcp-bus` e dentro dele um Event Hub chamado `stcp-telemetry`. Foi configurada uma política de acesso `RootManageSharedAccessKey`.

No Azure IoT Central foi configurada uma regra de exportação de dados que envia toda a telemetria recebida para o Event Hub em tempo real, no formato JSON.

As credenciais estão guardadas no ficheiro `.env` que não está no repositório por conter informação privada. Está listado no `.gitignore`.

### Fase 2 - Simulador Python

Foram criados três ficheiros:

`charging_station_simulator.py` contém a classe `ChargingStationSimulator`. Liga-se ao Azure IoT Central via DPS, envia telemetria a cada segundo e simula o comportamento físico do equipamento de carregamento.

`electric_bus_simulator.py` contém a classe `ElectricBusSimulator`. Liga-se da mesma forma, envia telemetria a cada segundo e simula o consumo de bateria, a temperatura e o movimento GPS do autocarro.

`main.py` é o orquestrador. Cria todas as instâncias, liga-as ao Azure em paralelo usando `asyncio`, e implementa a lógica básica de carregamento descrita na secção 4.4.

`config.py` contém a configuração partilhada: lista de dispositivos com IDs e chaves, localização do depósito e intervalo de telemetria.

### Fase 3 - Notebooks Azure Databricks

Foram criados 4 notebooks no Azure Databricks Community Edition:

**Notebook 1 - STCP Dados Simulados:** Configura a ligação ao Event Hub via Kafka, cria um Spark Streaming DataFrame que lê os dados em tempo real, faz o parse do JSON, separa os dados por tipo de dispositivo e escreve nas tabelas Delta `bus_telemetry` e `charger_telemetry`.

**Notebook 2 - STCP Business Rules:** Implementa 8 regras de negócio como queries SQL: limites de potência, prioridades de carregamento, limites de temperatura, disponibilidade de estações, distância ao depósito, tempo estimado de carregamento, balanceamento de carga e saúde da bateria.

**Notebook 3 - STCP Algoritmo de Decisão:** Algoritmo que combina as 8 regras para calcular um score de urgência para cada autocarro (máximo 100 pontos) e decidir automaticamente qual carregar, em qual estação e com que potência.

**Notebook 4 - STCP Simulação de Cenários:** Permite testar diferentes cenários manualmente para validar o comportamento do sistema.

### Fase 4 - Simplificação por indicação do orientador (estado actual)

O orientador indicou que o foco actual deve ser nas queries. O objectivo imediato é demonstrar que, com o simulador a correr e os dados a chegar ao Databricks, é possível responder a perguntas concretas sobre o estado da frota em tempo real.

---

## 6. Estado Actual do Projecto

| Componente | Estado |
|---|---|
| Azure IoT Central configurado | Concluído |
| Azure Event Hub configurado | Concluído |
| Simulador Python - 3 ficheiros criados | Concluído |
| Simulador Python - a correr e a enviar dados | Concluído |
| Databricks - ligação ao Event Hub | Concluído |
| Databricks - tabelas Delta criadas | Concluído |
| Databricks - regras de negócio | Concluído |
| Databricks - algoritmo de decisão | Concluído |
| Databricks - notebook de queries simples | Pendente |
| Integração GTFS (paragens reais) no simulador | Fase futura |

---

## 7. Passos Seguintes

**Passo 1 - Confirmar chegada de dados ao Databricks**

Com o simulador a correr no VS Code, abrir o Notebook 1 no Databricks e executar as células de stream. Verificar que os dados aparecem nas tabelas `bus_telemetry` e `charger_telemetry`.

**Passo 2 - Criar notebook de queries**

Criar um novo notebook no Databricks com queries SQL prontas para responder às perguntas do orientador sobre o estado actual da frota.

**Passo 3 - Demonstração ao orientador**

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

**Porquê `asyncio` no simulador Python?**

Os 6 dispositivos precisam de enviar telemetria em simultâneo, a cada segundo. O `asyncio` permite correr todas as tarefas de forma concorrente num único processo, sem criar 6 processos separados.

**Porquê o simulador não segue as paragens reais do GTFS nesta fase?**

A integração com os horários e coordenadas reais das linhas 200, 201 e 202 (disponíveis no ficheiro Excel do projecto) adiciona complexidade ao simulador que não é necessária para o objectivo actual de demonstrar queries. O movimento contínuo com descarga proporcional à distância é suficiente para mostrar que a bateria desce enquanto o autocarro está em rota. A integração GTFS está prevista para uma fase posterior.

---

*Documento actualizado à medida que o trabalho avança.*