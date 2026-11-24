# Diario de Trabalho - Projecto STCP
## Sistema de Monitorizacao de Carregamento de Autocarros Electricos

Autor: Luis Pereira
Instituicao: ISCAP
Ano: 2026
Repositorio: https://github.com/Highleaf2/stcp-bus-charging-simulation

---

## Indice

1. Contexto e Objectivo do Projecto
2. Arquitectura do Sistema
3. Dispositivos e Telemetria
4. O que o Simulador esta a Fazer
5. Registo Cronologico do Trabalho
6. Estado Actual do Projecto
7. Passos Seguintes
8. Decisoes Tecnicas e Justificacoes

---

## 1. Contexto e Objectivo do Projecto

O projecto tem como objectivo simular e monitorizar em tempo real o sistema de carregamento de autocarros electricos da STCP (Sociedade de Transportes Colectivos do Porto). O sistema permite acompanhar o estado da frota - nivel de bateria, localizacao GPS, estado das estacoes de carregamento - atraves de dados de telemetria enviados para a nuvem.

A arquitectura foi desenhada para simular, na fase academica, o que em producao seria feito por APIs e sensores reais instalados nos autocarros e nas estacoes de carregamento. Isto significa que o simulador Python e apenas temporario e substituivel, sem necessidade de alterar o resto da arquitectura.

Foco actual definido pelo orientador: queries. Com os dados a chegar ao Databricks em tempo real, o objectivo e conseguir responder a perguntas concretas sobre o estado da frota, como por exemplo:
- Qual o nivel de bateria do autocarro X neste momento?
- Onde esta o autocarro Y (coordenadas GPS)?
- Em que paragem esta o autocarro Z?
- Quantas paragens faltam para o autocarro terminar a rota?
- Qual a estacao de carregamento disponivel?
- Algum autocarro esta abaixo do nivel critico de bateria?
- Ha estacoes suficientes para todos os autocarros que precisam de carregar?

---

## 2. Arquitectura do Sistema

O sistema funciona em camadas. Cada camada tem uma responsabilidade especifica e e independente das restantes, o que significa que qualquer camada pode ser substituida sem afectar as outras.

```
[Python Simulador - VS Code] --> [Azure IoT Central] --> [Azure Event Hub] --> [Azure Databricks]
```

### Camada 1 - Simulador Python (PC Local / VS Code)

Ficheiros: charging_station_simulator.py, electric_bus_simulator.py, main.py, config.py

Funcao: Gerar dados simulados de telemetria e envia-los para o Azure IoT Central usando o protocolo MQTT via DPS. Cada dispositivo liga-se de forma independente e envia telemetria a cada 5 segundos.

Nota importante: No futuro, esta camada sera substituida por APIs reais dos autocarros e estacoes de carregamento da STCP. A arquitectura das camadas seguintes nao precisa de ser alterada.

### Camada 2 - Azure IoT Central

Conta: 2240115@iscap.ipp.pt (tenant BI4ALL)
Aplicacao: iotc-stcp-bus (iotc-stcp-bus.azureiotcentral.com)
ID Scope: 0ne0128409B

Nota: a conta e a aplicacao foram migradas da conta pessoal verbatim9898@proton.me (usada ate a Fase 10) para a conta institucional 2240115@iscap.ipp.pt, no ambito do resource group dedicado fornecido pela BI4ALL (ver Fase 12).

Funcao: Receber a telemetria de cada dispositivo, gerir a autenticacao via DPS, e exportar os dados em tempo real para o Event Hub. Apenas os campos definidos no device template de cada dispositivo sao exportados.

Nota sobre device templates e devices: Os device templates sao moldes que definem os campos de telemetria de cada tipo de dispositivo. Os devices sao os dispositivos individuais, cada um com a sua chave de autenticacao. Sao conceitos distintos: sem os templates o IoT Central nao sabe que campos esperar; sem os devices o simulador nao tem credenciais para se ligar.

### Camada 3 - Azure Event Hub

Namespace: ehns-stcp-bus
Nome do Event Hub: stcp-telemetry
Tier: Standard (obrigatorio para suporte Kafka na porta 9093)
Resource group: mrg-dbw-neu-dev-iscap_master_thesis_Eletric_Fleet
Conta Azure: 2240115@iscap.ipp.pt
Retencao: 1 hora

Funcao: Actua como fila de mensagens entre o IoT Central e o Databricks. Garante que nenhuma mensagem se perde mesmo que o Databricks esteja temporariamente indisponivel.

### Camada 4 - Azure Databricks

Workspace: dbw-stcp-bus
Cluster: stcp-cluster (Runtime 13.3 LTS, Single Node, termina apos 10 minutos de inactividade)
Resource group: mrg-dbw-neu-dev-iscap_master_thesis_Eletric_Fleet
Conta Azure: 2240115@iscap.ipp.pt (tenant BI4ALL)
Unity Catalog: activo

Funcao: Consome o stream de dados do Event Hub em tempo real, faz o parse do JSON, separa os dados por tipo de dispositivo, armazena em tabelas Delta permanentes e permite fazer queries SQL sobre os dados actuais e historicos.

### Service Principal

Nome: app-scap-master-thesis-Eletric-Fleet
Client ID: 73fc4958-0752-45a3-a153-187def960d20
Utilizacao: Lakeflow Zerobus Ingest

---

## 3. Dispositivos e Telemetria

### 3.1 Autocarros Electricos

Foram configurados 3 autocarros no Azure IoT Central com o template STCP_ELECTRIC_BUS:

| ID | Linha | Rota | Hora de Partida | Bateria Inicial | Estado Inicial | Distancia Inicial (m) |
|---|---|---|---|---|---|---|
| BUS-001 | Linha 200 | Bolhao - Castelo do Queijo | 08:30 | 45% (157,5 kWh) | inTransit | 8098,83 |
| BUS-002 | Linha 201 | Aliados - Viso | 09:00 | 70% (245 kWh) | inTransit | 696,96 |
| BUS-003 | Linha 202 | Aliados - Passeio Alegre | 07:45 | 25,3% (88,55 kWh) | inTransit | 5313,20 |

Os estados, niveis de bateria e distancias iniciais foram definidos com base na folha de configuracao do ficheiro Excel do projecto:
- BUS-001: faltam 5 paragens de 30, esta na paragem 25 (8098,83 metros percorridos)
- BUS-002: esta na segunda paragem (696,96 metros percorridos)
- BUS-003: a terminar a rota, perto da ultima paragem (5313,20 metros percorridos)

Especificacoes tecnicas (baseadas no CaetanoBus e.City Gold):

| Parametro | Valor |
|---|---|
| Capacidade da bateria | 350 kWh |
| Consumo medio | 1,2 kWh/km |
| Nivel minimo de seguranca | 20% |
| Nivel maximo de carregamento | 95% |
| Faixa operacional ideal | 20% a 80% |
| Potencia maxima de carregamento | 120 kW |

Telemetria enviada por cada autocarro a cada 5 segundos:

| Campo | Tipo | Descricao |
|---|---|---|
| batteryLevel | Double (%) | Estado de carga da bateria |
| batteryKwh | Double (kWh) | Energia disponivel na bateria |
| batteryTemperature | Double (Celsius) | Temperatura da bateria |
| latitude | Double | Coordenada GPS actual |
| longitude | Double | Coordenada GPS actual |
| instantConsumption | Double (kW) | Consumo instantaneo de energia |
| remainingRange | Double (km) | Autonomia restante estimada |
| state | Texto | Estado operacional actual |
| distanceTraveled | Double (metros) | Distancia percorrida na rota actual |

Estados possiveis de um autocarro:

| Estado | Descricao |
|---|---|
| parked | Estacionado no deposito |
| charging | Ligado a uma estacao de carregamento |
| inTransit | Em rota activa, a consumir bateria |

### 3.2 Estacoes de Carregamento

Foram configuradas 3 estacoes com estados distintos para simular um cenario realista, com o template STCP_CHARGING_STATIONS:

| ID | Estado Inicial | Descricao | Latitude | Longitude |
|---|---|---|---|---|
| CS-001 | occupied | A carregar o BUS-004 (autocarro ficticio) a 80 kW | 41.152661 | -8.579658 |
| CS-002 | fault | Com avaria, fora de servico | 41.152671 | -8.579668 |
| CS-003 | available | Disponivel para carregamento | 41.152681 | -8.579678 |

A localizacao corresponde ao deposito da STCP na Rua de Bojoia, Campanha, Porto.

O BUS-004 e um autocarro ficticio usado apenas para simular uma estacao ocupada. Nao existe como dispositivo no Azure IoT Central.

Limite total da rede electrica: 360 kW (soma das tres estacoes a 120 kW cada)

Telemetria enviada por cada estacao a cada 5 segundos:

| Campo | Tipo | Descricao |
|---|---|---|
| state | Texto | available, occupied ou fault |
| currentPower | Double (kW) | Potencia a ser entregue neste momento |
| currentEfficiency | Double (%) | Eficiencia actual do carregamento |
| chargerTemperature | Double (Celsius) | Temperatura do equipamento |
| energyDelivered | Double (kWh) | Energia entregue na sessao actual |
| connectedBus | Texto | ID do autocarro ligado (null se livre) |
| latitude | Double | Coordenada GPS da estacao |
| longitude | Double | Coordenada GPS da estacao |

Estados possiveis de uma estacao:

| Estado | Descricao |
|---|---|
| available | Livre, pronta para receber um autocarro |
| occupied | A carregar um autocarro activamente |
| fault | Com avaria, fora de servico |

---

## 4. O que o Simulador esta a Fazer

### 4.1 Arranque

Quando se executa python main.py, o programa cria 6 instancias de dispositivos e liga cada uma ao Azure IoT Central em paralelo usando asyncio.

### 4.2 Comportamento dos Autocarros

Quando esta em rota (estado inTransit):

A bateria desce continuamente com base na distancia percorrida. O campo distanceTraveled aumenta 50 metros por segundo (0,05 km/s). A cada segundo, o autocarro consome energia proporcional a distancia percorrida com base no consumo medio de 1,2 kWh/km. As coordenadas GPS mudam ligeiramente a cada leitura. A temperatura da bateria sobe gradualmente ate um maximo de 35 graus Celsius.

Nota: O consumo de bateria esta acelerado 10x propositadamente para fins de demonstracao, permitindo ver a bateria a descarregar visivelmente durante uma sessao curta. Isto e feito dividindo por 360 em vez de 3600 no calculo de consumo.

Nota: O GPS e aproximado e nao segue as coordenadas exactas das paragens GTFS. A paragem actual e determinada pelo campo distanceTraveled em comparacao com a tabela route_stops no Databricks.

Quando esta a carregar (estado charging):

A bateria sobe ao ritmo da potencia alocada com eficiencia de 92%. Para automaticamente aos 95%.

Quando esta estacionado (estado parked):

Auto-descarga muito pequena que simula o consumo dos sistemas em repouso.

### 4.3 Comportamento das Estacoes

Estado occupied (CS-001): Temperatura sobe ate maximo de 45 graus Celsius, energia acumula, eficiencia varia em torno dos 92%.

Estado fault (CS-002): Sem potencia, eficiencia a zero, temperatura mantem-se ligeiramente elevada.

Estado available (CS-003): Sem potencia, temperatura desce para 22 graus Celsius.

### 4.4 Tabela de Referencia das Paragens

Foi criada no Databricks uma tabela Delta estatica chamada route_stops com os horarios e coordenadas reais das paragens das tres linhas, obtidas da API publica da STCP (stcp.pt/api/route/{linha}/stops/direction):

- Linha 200 (BUS-001): 30 paragens, Bolhao ate Castelo do Queijo, 8.640,2 metros
- Linha 201 (BUS-002): 26 paragens, Aliados ate Viso, 8.389,7 metros
- Linha 202 (BUS-003): 30 paragens, Av. Aliados ate Passeio Alegre, 9.482,3 metros

Total: 86 paragens reais. Nota: a versao inicial desta tabela tinha apenas 72 paragens, porque faltavam as 14 primeiras paragens da Linha 202 (Av. Aliados ate Av. do Bessa) — corrigido na Fase 12.

Esta tabela permite cruzar a distancia percorrida em tempo real com as paragens reais para determinar onde cada autocarro esta na rota.

---

## 5. Registo Cronologico do Trabalho

### Fase 1 - Configuracao da Infraestrutura Azure

Criacao do Azure IoT Central (plano Trial) com 6 dispositivos e dois device templates: STCP Electric Bus e STCP Charging Station. Criacao do Azure Event Hub (plano Student) com namespace ehns-stcp-bus e Event Hub stcp-telemetry. Configuracao da regra de exportacao de dados no IoT Central.

### Fase 2 - Simulador Python (Versao Inicial)

Criacao dos ficheiros charging_station_simulator.py, electric_bus_simulator.py e main.py com orquestrador de carregamento automatico.

### Fase 3 - Notebooks Azure Databricks

Criacao de 4 notebooks: STCP Dados Simulados, STCP Business Rules, STCP Algoritmo de Decisao e STCP Simulacao de Cenarios.

### Fase 4 - Simplificacao por indicacao do orientador

Foco reduzido as queries. Notebooks 2, 3 e 4 colocados em segundo plano.

### Fase 5 - Correccao da Telemetria (30 de Marco de 2026)

Correccao de varios problemas: campo state a null (estava como propriedade em vez de telemetria), coordenadas GPS das estacoes a null (passaram para telemetria), autocarros sempre em parked (estados iniciais definidos no codigo com base no Excel), intervalo de telemetria alterado de 1 para 5 segundos.

### Fase 6 - Notebook de Queries Operacionais (30 de Marco de 2026)

Criacao do notebook STCP Queries organizado em quatro grupos:

Grupo 1 - Autocarros:
- Estado actual de todos os autocarros
- Autocarro com a bateria mais baixa
- Autocarros em nivel critico (abaixo de 20%)
- Autonomia restante de cada autocarro
- Vista completa de cada autocarro
- Evolucao da bateria do BUS-003

Grupo 2 - Estacoes de Carregamento:
- Estado actual de todas as estacoes
- Estacoes disponiveis para carregamento
- Estacoes com avaria

Grupo 3 - Servicos:
- Capacidade disponivel na rede de carregamento
- Tempo estimado para carregar cada autocarro ate 80%
- Autocarros que precisam de carregar antes da proxima rota
- Paragem mais proxima de cada autocarro (baseado em distanceTraveled)
- Quantas paragens faltam para cada autocarro terminar a rota

Grupo 4 - Queries Combinadas:
- Qual o autocarro que esta a ser carregado em cada estacao
- Ha estacoes suficientes para os autocarros que precisam de carregar?
- Custo estimado para carregar todos os autocarros ate 80%

Todas as queries usam ROW_NUMBER() OVER (PARTITION BY device_id ORDER BY event_time DESC) para garantir que apenas aparece o registo mais recente de cada dispositivo.

### Fase 7 - Cenario Realista nas Estacoes (30 de Marco de 2026)

Estados distintos nas estacoes: CS-001 occupied (a carregar BUS-004 ficticio), CS-002 fault (avaria), CS-003 available. Adicionado timeout de 60 segundos ao simulador.

### Fase 8 - Campo distanceTraveled e Tabela de Paragens (30 de Marco de 2026)

Adicionado o campo distanceTraveled a telemetria dos autocarros para rastrear a posicao na rota com precisao. Os valores iniciais de distancia foram definidos com base no estado descrito no Excel do projecto.

Criada a tabela Delta estatica route_stops no Databricks com os dados reais GTFS das tres linhas (72 paragens no total). Esta tabela permite determinar em que paragem esta cada autocarro e quantas paragens faltam para terminar a rota, cruzando o distanceTraveled em tempo real com as distancias reais das paragens.

### Fase 9 - Resource Group BI4ALL recebido (Junho de 2026)

A empresa BI4ALL forneceu um resource group dedicado para o projecto no ambito do mestrado:

- Nome do resource group: mrg-dbw-neu-dev-iscap_master_thesis_Eletric_Fleet
- Subscricao: Microsoft Azure Sponsorship - BI4ALL - K&I - CoEs - Data
- Subscription ID: 7791a09d-de4b-471d-9460-7265186677e8
- Localizacao: West Europe
- Conta Azure: 2240115@iscap.ipp.pt

### Fase 10 - Migracao Completa da Infraestrutura (5 de Junho de 2026)

Toda a infraestrutura foi recriada de raiz porque as contas anteriores (Azure for Students e conta Proton) expiraram.

IoT Central recriado:
- Conta: verbatim9898@proton.me
- Aplicacao: STCP Bus Charging
- ID Scope: 0ne011F5C22
- Device templates corrigidos e importados via JSON: STCP_ELECTRIC_BUS e STCP_CHARGING_STATIONS
- 6 dispositivos recriados: BUS-001, BUS-002, BUS-003, CS-001, CS-002, CS-003
- Exportacao de dados configurada para o Event Hub com estado healthy

Correccoes aplicadas aos device templates nesta migracao: campo state corrigido de Sate para state com schema string (estava com erro de digitacao e tipo errado), campo connectedBus corrigido de ConnectedBus para connectedBus com schema string, campos Latitude e Longitude corrigidos para minusculas. Estas correccoes evitam que os campos cheguem a null no Databricks.

Event Hub recriado:
- Namespace: ehns-stcp-bus
- Event Hub: stcp-telemetry
- Tier: Standard
- Retencao: 1 hora
- Resource group: mrg-dbw-neu-dev-iscap_master_thesis_Eletric_Fleet

Databricks recriado:
- Workspace: dbw-stcp-bus
- Cluster: stcp-cluster (Runtime 13.3 LTS, Single Node)
- Unity Catalog activo
- Resource group: mrg-dbw-neu-dev-iscap_master_thesis_Eletric_Fleet
- 5 notebooks importados: STCP Dados Simulados, STCP Queries, STCP Business Rules, STCP Algoritmo de Decisao, STCP Simulacao de Cenarios

Pipeline testado e validado:
- Simulador Python ligou os 6 dispositivos com sucesso
- Telemetria a chegar ao IoT Central
- Event Hub a receber dados com estado healthy
- Databricks a consumir o stream em tempo real
- Tabelas Delta bus_telemetry_raw e charger_telemetry_raw a receber dados
- Views bus_telemetry e charger_telemetry criadas com filtro de 2 minutos
- Notebook de queries executado com sucesso

Exploracao do Lakeflow Zerobus Ingest:
Foi explorado o Lakeflow Zerobus Ingest disponivel no workspace. Verificou-se que o Zerobus Ingest e um SDK para envio directo de dados para tabelas Delta a partir de produtores externos, substituindo potencialmente o IoT Central e o Event Hub. Requer um Service Principal Azure para autenticacao, que necessita de permissoes de administrador na subscricao da BI4ALL.

### Fase 11 - Service Principal, Novo Cluster e Seguranca do Repositorio (1 de Setembro de 2026)

Obtidas as credenciais do Service Principal para configuracao do Lakeflow Zerobus Ingest:
- Nome: app-scap-master-thesis-Eletric-Fleet
- Client ID: 73fc4958-0752-45a3-a153-187def960d20

Verificacao dos custos Azure no inicio desta fase:
- Event Hub: 6,08 euros
- Databricks: 0,00 euros (cluster estava inactivo)
- Orcamento definido: 100,00 euros
- Subscricao: Microsoft Azure Sponsorship - BI4ALL - K&I - CoEs - Data

O cluster stcp-cluster tinha expirado e foi recriado com as seguintes configuracoes:
- Runtime: 13.3 LTS (compativel com todos os notebooks existentes)
- Tipo: Single Node
- Desligamento automatico: 10 minutos de inactividade
- Unity Catalog: activo

Seguranca e limpeza do repositorio GitHub:
- Detectado que o ficheiro .env com credenciais do Azure IoT Central estava exposto no repositorio publico
- Criado ficheiro .gitignore com as seguintes exclusoes: .env, __pycache__/, *.pyc, backup_old/, *.ipynb_checkpoints
- Removido .env do tracking do Git com git rm --cached .env
- Removidas pastas __pycache__ e backup_old do tracking do Git com git rm --cached -r
- Alteracoes committed e pushed para o repositorio GitHub

### Fase 12 - Migracao final para a conta institucional e correcao das paragens (Outubro de 2026)

Nova migracao de infraestrutura, desta vez da conta pessoal verbatim9898@proton.me para a conta institucional 2240115@iscap.ipp.pt (tenant BI4ALL), que passou a ser usada em todas as camadas (IoT Central, Event Hub, Databricks):

- IoT Central recriado com a aplicacao iotc-stcp-bus (iotc-stcp-bus.azureiotcentral.com), ID Scope 0ne0128409B
- Mantidos os 6 dispositivos (BUS-001/002/003, CS-001/002/003) e os dois device templates

Correcao da tabela route_stops: a versao anterior tinha 72 paragens, incompleta para a Linha 202 (faltavam as 14 primeiras paragens, Av. Aliados ate Av. do Bessa). Foram obtidas as paragens completas das tres linhas directamente da API publica da STCP (stcp.pt/api/route/{linha}/stops/direction), totalizando 86 paragens reais (30 + 26 + 30). As distancias totais das rotas foram tambem corrigidas:
- Linha 200: 8.640,2 metros (30 paragens)
- Linha 201: 8.389,7 metros (26 paragens)
- Linha 202: 9.482,3 metros (30 paragens, agora completa desde Av. Aliados)

O simulador (electric_bus_simulator.py) e o ficheiro config.py foram actualizados para usar os nomes de rota reais (Route-200, Route-201, Route-202, em vez dos nomes placeholder Route-700/800/900 de versoes anteriores).

### Fase 13 - Consolidacao dos notebooks finais e resultados da dissertacao (Outubro de 2026)

Os cinco notebooks foram consolidados nas versoes _FINAL, usadas directamente para gerar os resultados reportados na dissertacao (Capitulo IV):
- 1 - STCP_Dados_Simulados_FINAL.ipynb (ingestao e streaming)
- 1.1 - STCP Queries_FINAL.ipynb (17 queries operacionais em 4 grupos: Autocarros, Estacoes, Servicos, Combinadas)
- 2_STCP_Business_Rules_FINAL.ipynb (8 regras de negocio)
- 3 - STCP Algoritmo de Decisao_FINAL.ipynb (algoritmo de decisao em 7 fases + Fase 8 de alertas)
- 4 - STCP Simulacao de Cenarios_FINAL.ipynb (6 cenarios controlados + sub-cenarios 6A/6B)

As versoes anteriores destes notebooks foram preservadas nas pastas Old/ e Old Notebooks/, para manter o historico do trabalho.

Resultados principais obtidos com dados reais de telemetria (600 eventos): latencia mediana de ingestao de 2 segundos (P95: 5 segundos). Na analise de custos, o Azure Cost Management reportou 0,00 euros para o Databricks no periodo analisado — mas este valor deve ser lido com cautela, por causa da latencia de reporte da facturacao de DBU; com os dados disponiveis, e o Event Hub que domina o custo real do projecto, por ser facturado de forma continua enquanto o namespace esta provisionado, ao contrario do cluster Databricks (Single Node, desligamento automatico ao fim de 10 minutos de inactividade).

Nota sobre o Lakeflow Zerobus Ingest (explorado na Fase 10 como trabalho futuro): o Zerobus Ingest atingiu disponibilidade geral apenas em fevereiro de 2026, depois da implementacao deste projecto. Continua a ser uma alternativa valida ao par IoT Central + Event Hub a considerar no futuro, visto o Databricks ser o unico consumidor dos dados de telemetria.

### Fase 14 - Sincronizacao final do repositorio GitHub (Novembro de 2026)

O repositorio publico estava desactualizado: tinha ainda os notebooks anteriores aos _FINAL, e nao reflectia as alteracoes ao simulador Python feitas na Fase 12. Foi feito commit e push do estado final: notebooks _FINAL, pastas Old/Old Notebooks preservadas, exports dos dashboards Lakeview, tabela route_stops e as alteracoes a electric_bus_simulator.py, config.py, charging_station_simulator.py e main.py.

---

## 6. Estado Actual do Projecto

| Componente | Estado |
|---|---|
| Azure IoT Central configurado | Concluido (2240115@iscap.ipp.pt, tenant BI4ALL) |
| Azure Event Hub configurado | Concluido (resource group BI4ALL) |
| Device templates corrigidos e importados | Concluido |
| 6 dispositivos criados e autenticados | Concluido |
| Exportacao IoT Central para Event Hub | Concluido (estado healthy) |
| Simulador Python - telemetria completa | Concluido |
| Simulador Python - campo distanceTraveled | Concluido |
| Simulador Python - estados realistas nas estacoes | Concluido |
| Simulador Python - consumo acelerado 10x para demonstracao | Concluido |
| Databricks - workspace no resource group BI4ALL | Concluido |
| Databricks - cluster stcp-cluster activo | Concluido |
| Databricks - Unity Catalog activo | Concluido |
| Databricks - tabelas Delta a receber dados em tempo real | Concluido |
| Databricks - tabela route_stops com dados reais (86 paragens) | Concluido |
| Databricks - notebook de queries grupo 1 (Autocarros) | Concluido |
| Databricks - notebook de queries grupo 2 (Estacoes) | Concluido |
| Databricks - notebook de queries grupo 3 (Servicos) | Concluido |
| Databricks - notebook de queries grupo 4 (Combinadas) | Concluido |
| Notebook de regras de negocio (8 regras) | Concluido |
| Notebook de algoritmo de decisao (7 fases + Fase 8 alertas) | Concluido |
| Notebook de simulacao de cenarios (6 cenarios + 6A/6B) | Concluido |
| Pipeline completo testado e validado com dados reais | Concluido |
| Analise de custos e sensibilidade a frequencia de telemetria | Concluido |
| Resultados reportados na dissertacao (Capitulo IV) | Concluido |
| Dissertacao submetida e aprovada pela orientadora | Concluido |
| Repositorio GitHub sincronizado com a versao final | Concluido |
| Service Principal obtido | Concluido |
| Lakeflow Zerobus Ingest configurado | Pendente (trabalho futuro — atingiu disponibilidade geral so depois deste projecto) |

---

## 7. Passos Seguintes

O trabalho principal esta concluido: a dissertacao foi submetida e aprovada pela orientadora, e os resultados do Capitulo IV foram todos obtidos com dados reais de telemetria. Os passos seguintes dizem respeito a defesa e a trabalho futuro identificado no Capitulo V.

### Passo 1 - Preparacao da defesa

Ensaiar a apresentacao (20 minutos), preparar respostas a perguntas provaveis, e gravar um video curto do simulador a correr com os dados a chegar ao Databricks em tempo real.

### Passo 2 - Resolver as tensoes entre regras de negocio

Unificar os criterios de avaliacao do estado da rede (RN-07) e da disponibilidade de estacoes (Notebook 1.1), e ajustar a formula do indicador de pressao da frota (Π) para distinguir explicitamente zero estacoes disponiveis de uma estacao disponivel.

### Passo 3 - Avaliar o Lakeflow Zerobus Ingest

Com o Service Principal ja obtido (Client ID: 73fc4958-0752-45a3-a153-187def960d20), avaliar o Zerobus Ingest (disponibilidade geral desde fevereiro de 2026) como alternativa directa ao par IoT Central + Event Hub, eliminando o componente que actualmente domina o custo real da solucao.

### Passo 4 - Melhorias futuras identificadas no Capitulo V

- Implementar um canal de notificacao real (Azure Logic Apps ou Databricks Workflows) sobre a tabela alertas_operacionais
- Validacao quantitativa da escalabilidade, latencia e custo a escala de uma frota de producao (126 veiculos)
- Comparacao empirica entre as regras de negocio pontuadas e modelos de optimizacao formal da literatura
- Mecanismo de prioridade absoluta para veiculos externos a frota normal (ex: reforcos de emergencia)
- Visualizacao geografica no dashboard (Azure Maps ou Kepler.gl) e actualizacao autonoma agendada
- Substituicao do simulador Python por APIs reais dos autocarros e estacoes da STCP

---

## 8. Decisoes Tecnicas e Justificacoes

Porque Azure IoT Central e nao envio directo para o Databricks?

O Azure IoT Central serve como camada de gestao de dispositivos. No futuro, quando os autocarros tiverem sensores reais, estes vao comunicar com o IoT Central directamente. Manter esta arquitectura agora significa que a transicao do simulador para o sistema real nao exige nenhuma alteracao no Databricks.

Porque Event Hub como intermediario?

O Event Hub actua como buffer entre o IoT Central e o Databricks. Permite que o Databricks consuma os dados ao seu ritmo sem perder mensagens.

Porque protocolo Kafka no Event Hub?

O Azure Event Hub e compativel com o protocolo Kafka, que e o protocolo nativo do Spark Streaming no Databricks. Esta compatibilidade elimina a necessidade de bibliotecas adicionais.

Porque o Event Hub tem de ser Standard e nao Basic?

O plano Basic nao suporta o protocolo Kafka na porta 9093. O Databricks Spark Streaming usa Kafka para consumir dados do Event Hub. Com o plano Basic a ligacao falha com erro de conectividade.

Porque tabelas Delta e nao simples tabelas Spark?

As tabelas Delta permitem leituras e escritas simultaneas, essencial para monitorizacao em tempo real.

Porque asyncio no simulador Python?

Os 6 dispositivos precisam de enviar telemetria em simultaneo. O asyncio permite correr todas as tarefas de forma concorrente num unico processo.

Porque as coordenadas das estacoes sao enviadas como telemetria e nao como propriedades?

As propriedades do dispositivo nao sao exportadas pelo IoT Central para o Event Hub, por isso chegavam sempre a null no Databricks. A solucao foi inclui-las na telemetria.

Porque o campo distanceTraveled em vez de usar apenas o GPS?

O GPS simulado e aproximado e nao coincide com as coordenadas reais das paragens. O campo distanceTraveled acumula a distancia percorrida desde o inicio da rota e permite determinar com precisao em que paragem esta o autocarro, cruzando com as distancias reais das paragens na tabela route_stops.

Porque a tabela route_stops e estatica no Databricks e nao vem do IoT Central?

Os horarios e paragens sao dados de referencia fixos que nunca mudam. O Azure IoT Central e para telemetria de dispositivos em tempo real. Guardar dados estaticos no Databricks e a abordagem correcta e permite fazer JOINs eficientes com os dados em tempo real.

Porque o BUS-004 e ficticio?

O BUS-004 existe apenas como valor no campo connectedBus da CS-001 para simular uma estacao ocupada. Criar um dispositivo real no IoT Central seria desnecessario para o objectivo actual de demonstrar queries.

Porque o consumo de bateria esta acelerado 10x?

Para fins de demonstracao. Com consumo real, a bateria levaria horas a descarregar visivelmente. Com aceleracao 10x (divisor 360 em vez de 3600), e possivel observar a descarga durante uma sessao curta de demonstracao.

Porque o orquestrador de carregamento foi removido?

O foco actual sao as queries. O orquestrador adicionava complexidade e provocava mudancas de estado automaticas que dificultavam a demonstracao. Os estados sao definidos directamente no codigo com base no cenario do Excel.

Diferenca entre device templates e devices no IoT Central:

Os device templates sao moldes que definem os campos de telemetria e propriedades de um tipo de dispositivo. Os devices sao as instancias individuais, cada uma com a sua propria chave de autenticacao gerada pelo DPS. Sem os templates o IoT Central nao sabe que campos exportar; sem os devices o simulador nao tem credenciais para se ligar. Sao dois passos obrigatorios e distintos na configuracao.

Porque os checkpoints do Databricks usam dbfs:/Workspace/checkpoints/ e nao /tmp/checkpoint/?

O DBFS publico pode estar desactivado no workspace da BI4ALL. O caminho dbfs:/Workspace/checkpoints/ e mais seguro e compativel com o Unity Catalog activo.

Porque as tabelas Delta sao nomeadas com sufixo _raw e existe uma view separada?

As tabelas _raw guardam todos os dados recebidos, incluindo mensagens antigas que ficam retidas no Event Hub. As views filtram apenas os ultimos 5 minutos, garantindo que as queries operacionais mostram sempre o estado actual e nao dados antigos.

Porque e que o Databricks aparece com custo 0,00 euros, se e a plataforma central do sistema?

Porque o cluster Single Node se desliga automaticamente ao fim de 10 minutos de inactividade, e a facturacao de DBU no Azure Cost Management tem uma latencia de reporte tipica — o valor deve ser lido com cautela, nao significa necessariamente custo zero real. Com os dados disponiveis, e na verdade o Event Hub que domina o custo total do projecto, por ser facturado de forma continua enquanto o namespace estiver provisionado, ao contrario do cluster Databricks.

---

Documento actualizado a medida que o trabalho avanca. Ultima actualizacao: 24 de Novembro de 2026 (apos a submissao e aprovacao da dissertacao, em preparacao para a defesa).
