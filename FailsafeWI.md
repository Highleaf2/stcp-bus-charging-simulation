# Guia de Recuperação da Infraestrutura - STCP Bus Charging

Este documento descreve todos os passos necessários para recriar toda a infraestrutura do projecto de raiz, caso as contas expirem ou os recursos sejam apagados.

Última actualização: 5 de Junho de 2026

---

## Contas Necessárias

Antes de começar, confirma que tens acesso a estas contas:

| Conta | Utilização |
|---|---|
| verbatim9898@proton.me | Azure IoT Central |
| 2240115@iscap.ipp.pt | Azure Portal (Event Hub + Databricks via BI4ALL) |

---

## Parte 1 - Azure IoT Central

### 1.1 Criar a Aplicação

1. Abre o browser e vai a `https://apps.azureiotcentral.com`
2. Inicia sessão com `verbatim9898@proton.me`
3. Clica em **New application**
4. Preenche os campos:
   - Application name: `STCP Bus Charging`
   - URL: `stcp-bus-charging` (se estiver ocupado tenta `stcp-bus-charging-2` ou similar)
   - Application template: `Custom application`
   - Pricing plan: `Standard 2`
   - Directory: o que aparecer por defeito
   - Azure subscription: o que aparecer por defeito
   - Location: `West Europe`
5. Clica em **Create**

### 1.2 Criar os Device Templates

Os device templates definem os campos de telemetria de cada tipo de dispositivo. Tens de criar dois: um para autocarros e outro para estações.

Os ficheiros JSON dos templates estão no repositório GitHub em `STCP_Electric_Bus.json` e `STCP_Charging_Station.json`. Estes ficheiros ja estao corrigidos e prontos a usar.

Para importar cada template:

1. No menu esquerdo do IoT Central clica em **Device templates**
2. Clica em **New**
3. Clica em **Import a model**
4. Faz upload do ficheiro `STCP_Electric_Bus.json`
5. Clica em **Publish**
6. Repete os passos 2 a 5 para o ficheiro `STCP_Charging_Station.json`

Quando terminares deves ter dois templates publicados: `STCP_ELECTRIC_BUS` e `STCP_CHARGING_STATIONS`.

### 1.3 Criar os 6 Dispositivos

Para cada dispositivo:

1. No menu esquerdo clica em **Devices**
2. Clica em **New**
3. Preenche os campos e clica em **Create**

Cria os seguintes dispositivos:

| Device name | Device ID | Device template |
|---|---|---|
| BUS-001 | BUS-001 | STCP_ELECTRIC_BUS |
| BUS-002 | BUS-002 | STCP_ELECTRIC_BUS |
| BUS-003 | BUS-003 | STCP_ELECTRIC_BUS |
| CS-001 | CS-001 | STCP_CHARGING_STATIONS |
| CS-002 | CS-002 | STCP_CHARGING_STATIONS |
| CS-003 | CS-003 | STCP_CHARGING_STATIONS |

### 1.4 Obter as Credenciais dos Dispositivos

Para cada um dos 6 dispositivos:

1. Clica no nome do dispositivo
2. Clica em **Connect** (canto superior direito)
3. Anota o **ID Scope** (igual para todos) e a **Primary Key** (diferente para cada dispositivo)

Guarda estes valores — vais precisar deles para actualizar o ficheiro `.env` no PC.

### 1.5 Configurar a Exportação de Dados para o Event Hub

Esta configuração envia a telemetria do IoT Central para o Event Hub automaticamente.

1. No menu esquerdo clica em **Data export**
2. Clica em **+ New export**
3. Preenche os campos:
   - Export name: `STCP Telemetry Export`
   - Data: selecciona **Telemetry**
4. Em **Destinations** clica em **+ Add destination**
5. Preenche os campos:
   - Destination name: `Event Hub STCP`
   - Destination type: `Azure Event Hubs`
   - Connection string: cola a connection string do Event Hub (ver Parte 2)
   - Event Hub: `stcp-telemetry`
6. Clica em **Save** na destination
7. Clica em **Save** no export

Aguarda alguns segundos. O estado deve ficar **healthy**. Se não ficar, verifica se a connection string do Event Hub esta correcta.

---

## Parte 2 - Azure Event Hub

### 2.1 Criar o Namespace

1. Abre o browser e vai a `https://portal.azure.com`
2. Inicia sessão com `2240115@iscap.ipp.pt`
3. Na barra de pesquisa no topo escreve **Event Hubs** e clica
4. Clica em **Create**
5. Preenche os campos:
   - Subscription: `Microsoft Azure Sponsorship - BI4ALL - K&I - CoEs - Data`
   - Resource group: `mrg-dbw-neu-dev-iscap_master_thesis_Eletric_Fleet`
   - Namespace name: `ehns-stcp-bus`
   - Location: `West Europe`
   - Pricing tier: `Standard` (obrigatorio - o Basic nao suporta Kafka)
6. Clica em **Review + create** e depois **Create**
7. Aguarda a criação (cerca de 1 minuto)

### 2.2 Criar o Event Hub

1. Abre o namespace `ehns-stcp-bus` que acabaste de criar
2. No menu esquerdo clica em **Event Hubs**
3. Clica em **+ Event Hub**
4. Preenche os campos:
   - Name: `stcp-telemetry`
   - Partition count: `2`
   - Retention: `1 hora`
5. Clica em **Review + create** e depois **Create**

### 2.3 Obter a Connection String

Esta connection string e necessaria para o IoT Central e para o Databricks.

1. Ainda dentro do namespace `ehns-stcp-bus`
2. No menu esquerdo clica em **Shared access policies**
3. Clica em **RootManageSharedAccessKey**
4. Copia o valor de **Connection string-primary key**

O formato e:
```
Endpoint=sb://ehns-stcp-bus.servicebus.windows.net/;SharedAccessKeyName=RootManageSharedAccessKey;SharedAccessKey=CHAVE_AQUI
```

Guarda este valor - precisas dele no passo 1.5 (exportacao IoT Central) e no notebook do Databricks.

---

## Parte 3 - Azure Databricks

### 3.1 Criar o Workspace

1. Ainda no `https://portal.azure.com` com a conta `2240115@iscap.ipp.pt`
2. Na barra de pesquisa escreve **Azure Databricks** e clica
3. Clica em **Create**
4. Preenche os campos:
   - Subscription: `Microsoft Azure Sponsorship - BI4ALL - K&I - CoEs - Data`
   - Resource group: `mrg-dbw-neu-dev-iscap_master_thesis_Eletric_Fleet`
   - Workspace name: `dbw-stcp-bus`
   - Region: `West Europe`
   - Pricing tier: `Trial Premium` se disponivel, senao `Standard`
5. Clica em **Review + create** e depois **Create**
6. Aguarda o deployment (2 a 3 minutos)
7. Clica em **Go to resource** e depois em **Launch Workspace**

### 3.2 Criar o Cluster

1. No menu esquerdo do Databricks clica em **Compute**
2. Clica em **Create compute**
3. Preenche os campos:
   - Policy: `Unrestricted`
   - Cluster name: `stcp-cluster`
   - Cluster mode: `Single node`
   - Databricks runtime version: `13.3 LTS (Scala 2.12, Spark 3.4.1)`
   - Node type: o mais pequeno disponivel (normalmente `Standard_DS3_v2`)
   - Terminate after: `30 minutes`
4. Clica em **Create compute**
5. Aguarda o cluster ficar verde (3 a 5 minutos)

### 3.3 Importar os Notebooks

Os notebooks estao no repositorio GitHub `https://github.com/Highleaf2/stcp-databricks-notebooks`.

Para cada notebook:

1. No menu esquerdo clica em **Workspace**
2. Clica em **+ New** e selecciona **Import**
3. Selecciona **URL** e cola o link directo do notebook no GitHub, ou faz upload do ficheiro `.ipynb`

Os notebooks a importar sao:
- `1_-_STCP_Dados_Simulados.ipynb` (este e o notebook de streaming - usa a versao corrigida)
- `1_1_-_STCP_Queries.ipynb`
- `2-_STCP_Business_Rules.ipynb`
- `3_-_STCP_Algoritmo_de_Decisao.ipynb`
- `4_-_STCP_Simulacao_de_Cenarios.ipynb`

### 3.4 Actualizar a Chave do Event Hub no Notebook de Streaming

O notebook `1 - STCP Dados Simulados` tem a chave do Event Hub hardcoded. Sempre que o Event Hub for recriado, a chave muda e tens de actualizar o notebook.

1. Abre o notebook `1 - STCP Dados Simulados`
2. Procura a celula com `eh_key = "..."` (Passo 1 - Configuracao Event Hub)
3. Substitui o valor pelo novo que copiaste no passo 2.3
4. Confirma que `eh_key_name = "RootManageSharedAccessKey"` (nao "Manage")
5. Confirma que os checkpoints usam `dbfs:/Workspace/checkpoints/` e nao `/tmp/checkpoint/`

### 3.5 Recriar a Tabela route_stops

Esta tabela contem as paragens reais GTFS das tres linhas e e necessaria para as queries de localizacao. Tem de ser recriada manualmente porque e uma tabela estatica.

O codigo para criar esta tabela esta no notebook `1 - STCP Dados Simulados` na seccao "Horario de cada autocarro". Executa essa celula uma vez para criar a tabela.

---

## Parte 4 - Actualizar o Ficheiro .env no PC

O ficheiro `.env` esta em:
```
C:\Users\luisi\Desktop\Tese - Claude\stcp-bus-charging-simulation\.env
```

Abre o ficheiro no VS Code e substitui o conteudo com as novas credenciais:

```
ID_SCOPE=ID_SCOPE_AQUI

BUS_001_KEY=CHAVE_BUS001_AQUI
BUS_002_KEY=CHAVE_BUS002_AQUI
BUS_003_KEY=CHAVE_BUS003_AQUI

CS_001_KEY=CHAVE_CS001_AQUI
CS_002_KEY=CHAVE_CS002_AQUI
CS_003_KEY=CHAVE_CS003_AQUI
```

Substitui cada valor pelo que copiaste no passo 1.4.

Guarda o ficheiro com Ctrl+S.

---

## Parte 5 - Testar o Pipeline Completo

Segue estes passos pela ordem indicada para verificar que tudo esta a funcionar.

**Passo 1 - Arrancar o simulador**

Abre o VS Code, abre o terminal (menu Terminal > New Terminal) e corre:

```
cd "C:\Users\luisi\Desktop\Tese - Claude\stcp-bus-charging-simulation"
python main.py
```

Deves ver:
```
Connected: CS-001 (occupied)
Connected: CS-002 (fault)
Connected: CS-003 (available)
Connected: BUS-001 (inTransit)
Connected: BUS-002 (inTransit)
Connected: BUS-003 (inTransit)
```

Se aparecer `Credentials invalid` ou `status code 401`, as chaves no `.env` estao erradas. Verifica o passo 1.4 e 4.

**Passo 2 - Verificar o IoT Central**

No IoT Central, vai a **Devices** e verifica que os dispositivos mostram estado **Provisioned** (em vez de apenas Registered). Isto confirma que o simulador se ligou com sucesso.

**Passo 3 - Executar o notebook de streaming no Databricks**

Com o simulador ainda a correr:

1. Abre o Databricks e o notebook `1 - STCP Dados Simulados`
2. Confirma que esta ligado ao cluster `stcp-cluster`
3. Executa as celulas pela ordem:
   - Celula de configuracao do Event Hub - deve aparecer "Configuracao concluida com sucesso"
   - Celula de leitura do stream - deve aparecer "Stream configurado!"
   - Celula de parse do JSON - deve aparecer "Schema actualizado com distanceTraveled!"
   - Celula de gravacao nas tabelas Delta - deve aparecer dois streams activos com "Last updated: X seconds ago"
   - Celula de criacao das views
4. Executa as celulas de verificacao de dados - devem aparecer registos das estacoes e autocarros

**Passo 4 - Executar o notebook de queries**

1. Abre o notebook `1_1 - STCP Queries`
2. Executa todas as celulas
3. Cada query deve devolver resultados com dados reais dos 6 dispositivos

Se tudo correu bem, o pipeline esta completo e funcional.

---

## Erros Comuns e Solucoes

**Erro: Credentials invalid / status code 401**

As chaves no ficheiro `.env` estao erradas ou desactualizadas. Vai ao IoT Central, clica em cada dispositivo, clica em Connect e copia a Primary Key correcta para o `.env`.

**Erro: status code 409 ao criar a aplicacao IoT Central**

O URL ja esta em uso por uma aplicacao anterior. Muda o URL para algo diferente (ex: `stcp-bus-charging-2`).

**Erro: Connection refused ao ligar ao Event Hub no Databricks**

O Event Hub foi criado com o plano Basic em vez de Standard. O plano Basic nao suporta Kafka. Apaga o namespace e recria com o plano Standard.

**Erro: checkpoint path nao encontrado no Databricks**

O notebook esta a usar `/tmp/checkpoint/` em vez de `dbfs:/Workspace/checkpoints/`. Corrige os caminhos no notebook.

**Dados a null no Databricks (state, connectedBus, latitude, longitude)**

Os device templates tem esses campos definidos como propriedades em vez de telemetria. Usa os ficheiros JSON corrigidos do repositorio para importar os templates.

**Dispositivos em estado Registered e nao Provisioned**

As chaves estao trocadas entre dispositivos. Vai ao Connect de cada dispositivo no IoT Central e confirma qual a chave de cada um. Actualiza o `.env` com as chaves correctas para cada ID.

---

## Referências

- Repositorio GitHub simuladores: `https://github.com/Highleaf2/stcp-bus-charging-simulation`
- Repositorio GitHub notebooks: `https://github.com/Highleaf2/stcp-databricks-notebooks`
- Azure IoT Central: `https://apps.azureiotcentral.com`
- Azure Portal: `https://portal.azure.com`
- Resource group BI4ALL: `mrg-dbw-neu-dev-iscap_master_thesis_Eletric_Fleet`
- Subscription ID BI4ALL: `7791a09d-de4b-471d-9460-7265186677e8`
