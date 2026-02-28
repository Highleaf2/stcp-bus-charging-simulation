# Configuração com config.py - Guia de Instalação

## ✅ O Que Foi Alterado

O `main_realistic.py` agora usa o `config.py` em vez de credenciais hardcoded no código.

### **Antes**
```python
# Credenciais no código
ID_SCOPE = "0ne00B37E67"
PRIMARY_KEY = "RobYA6qrRAa0bUkk/wX6YVKGIWJoIbJTNPEa6y7o5Xw="
BUS_IDS = ["BUS-001", "BUS-002", "BUS-003"]
```

### **Agora**
```python
# Importa do config.py
import config
ID_SCOPE = config.ID_SCOPE
BUS_IDS = list(config.ELECTRIC_BUSES.keys())
```

---

## 📁 Estrutura de Ficheiros

```
STCP-BUS-CHARGING-SIMULATION/
├── .env                        ← NOVO! Credenciais aqui
├── config.py                   ← Já tens (lê o .env)
├── bus_simulator.py            ← Novo
├── charger_simulator.py        ← Novo
├── main_realistic.py           ← Atualizado (usa config.py)
├── requirements.txt
└── README.md
```

---

## 🔧 Passo a Passo

### **Passo 1: Adicionar Ficheiro .env**

Cria um ficheiro chamado `.env` na raiz do projeto com este conteúdo:

```env
# Azure IoT Central Configuration
ID_SCOPE=0ne00B37E67

# Charging Station Keys
CS_001_KEY=RobYA6qrRAa0bUkk/wX6YVKGIWJoIbJTNPEa6y7o5Xw=
CS_002_KEY=RobYA6qrRAa0bUkk/wX6YVKGIWJoIbJTNPEa6y7o5Xw=
CS_003_KEY=RobYA6qrRAa0bUkk/wX6YVKGIWJoIbJTNPEa6y7o5Xw=

# Electric Bus Keys
BUS_001_KEY=RobYA6qrRAa0bUkk/wX6YVKGIWJoIbJTNPEa6y7o5Xw=
BUS_002_KEY=RobYA6qrRAa0bUkk/wX6YVKGIWJoIbJTNPEa6y7o5Xw=
BUS_003_KEY=RobYA6qrRAa0bUkk/wX6YVKGIWJoIbJTNPEa6y7o5Xw=
```

**⚠️ Importante**: 
- No VS Code, clica em "New File" na raiz do projeto
- Chama exatamente `.env` (com o ponto no início!)
- Cola o conteúdo acima

---

### **Passo 2: Verificar python-dotenv**

O `config.py` usa `python-dotenv` para ler o `.env`. Verifica se está instalado:

```bash
pip list | grep python-dotenv
```

Se **não estiver**, instala:

```bash
pip install python-dotenv
```

Ou adiciona ao `requirements.txt`:
```txt
azure-iot-device
python-dotenv
```

---

### **Passo 3: Substituir main_realistic.py**

Substitui o `main_realistic.py` antigo pelo novo que te enviei (já usa `config.py`).

---

### **Passo 4: Executar**

```bash
python main_realistic.py
```

---

## 🔐 Segurança

### **Vantagens desta Abordagem**

✅ **Credenciais no .env** - Não estão no código
✅ **Fácil partilhar código** - Podes partilhar sem expor chaves
✅ **Gitignore .env** - Adiciona `.env` ao `.gitignore`:

```
# .gitignore
.env
__pycache__/
*.pyc
venv/
```

---

## 📝 Notas Técnicas

### **Como Funciona**

1. `.env` contém as credenciais
2. `config.py` lê o `.env` com `python-dotenv`
3. `main_realistic.py` importa `config.py`
4. Cada dispositivo usa a sua chave específica

### **Chaves Partilhadas**

Neste momento, **todos os dispositivos** usam a **mesma chave primária** (Group Enrollment key do IoT Central).

Se quiseres chaves individuais:
1. No IoT Central, vai a cada dispositivo
2. Copia a "Primary Key" individual
3. Substitui no `.env`

---

## 🐛 Troubleshooting

### **Erro: "No module named 'dotenv'"**
```bash
pip install python-dotenv
```

### **Erro: "ID_SCOPE is None" ou "your-id-scope-here"**
O `.env` não foi carregado. Verifica:
- Ficheiro chama-se exatamente `.env` (com ponto)
- Está na **mesma pasta** que `config.py` e `main_realistic.py`
- Tem as variáveis sem espaços: `ID_SCOPE=valor` (não `ID_SCOPE = valor`)

### **Erro: "your-key-here"**
As chaves no `.env` não foram configuradas. Copia do ficheiro `.env` que te enviei.

---

## ✅ Verificação Final

Antes de executar, confirma:

- [ ] Ficheiro `.env` criado na raiz do projeto
- [ ] `python-dotenv` instalado
- [ ] `main_realistic.py` atualizado (importa `config`)
- [ ] `config.py` já existente (não mexer)

---

Tudo pronto! Executa:
```bash
python main_realistic.py
```