"""
Gerar Excel com Regras de Negócio - Sistema STCP
"""

import pandas as pd
from datetime import datetime

# Criar writer Excel
output_file = "STCP_Regras_Negocio.xlsx"
writer = pd.ExcelWriter(output_file, engine='openpyxl')

# SHEET 1: Resumo das Regras
regras_resumo = pd.DataFrame({
    'ID': ['R1', 'R2', 'R3', 'R4', 'R5', 'R6', 'R7', 'R8'],
    'Nome': [
        'Limites de Potência',
        'Prioridades de Carregamento',
        'Limites de Temperatura',
        'Disponibilidade de Estações',
        'Distância ao Depósito',
        'Tempo Estimado de Carregamento',
        'Balanceamento de Carga',
        'Saúde da Bateria'
    ],
    'Tipo': [
        'Simples',
        'Complexa',
        'Simples',
        'Simples',
        'Complexa',
        'Complexa',
        'Complexa',
        'Simples'
    ],
    'Prioridade': [
        'Crítica',
        'Alta',
        'Crítica',
        'Média',
        'Alta',
        'Média',
        'Alta',
        'Baixa'
    ],
    'Descrição': [
        'Não exceder potência máxima de carregamento da estação',
        'Ajustar potência com base nas prioridades de cada veículo',
        'Monitorizar temperatura de baterias e carregadores',
        'Verificar disponibilidade de estações para alocação',
        'Verificar se autocarro consegue chegar ao depósito',
        'Calcular tempo necessário para carregar cada autocarro',
        'Distribuir carga entre estações sem sobrecarregar rede',
        'Monitorizar ciclos de carga e degradação da bateria'
    ]
})
regras_resumo.to_excel(writer, sheet_name='Resumo', index=False)

# SHEET 2: Regra 1 - Limites de Potência
r1_parametros = pd.DataFrame({
    'Parâmetro': [
        'Potência máxima por estação',
        'Bateria máxima autocarro',
        'Nível crítico bateria',
        'Nível ideal bateria'
    ],
    'Valor': [150.0, 350.0, 20.0, 80.0],
    'Unidade': ['kW', 'kWh', '%', '%'],
    'Descrição': [
        'Potência máxima que cada estação pode fornecer',
        'Capacidade total da bateria de cada autocarro',
        'Nível abaixo do qual é crítico carregar',
        'Nível ideal para operação normal'
    ]
})
r1_parametros.to_excel(writer, sheet_name='R1_Limites_Potencia', index=False)

# SHEET 3: Regra 2 - Prioridades
r2_prioridades = pd.DataFrame({
    'Autocarro': ['BUS-001', 'BUS-002', 'BUS-003'],
    'Rota ID': ['200', '201', '202'],
    'Rota Nome': [
        'Bolhão - Castelo Queijo',
        'Aliados - Viso',
        'Aliados - Passeio Alegre'
    ],
    'Prioridade': ['Alta', 'Normal', 'Crítica'],
    'Distância (km)': [9.85, 9.78, 5.31],
    'Bateria Mínima Requerida (%)': [30.0, 30.0, 20.0],
    'Score Prioridade': [30, 20, 40]
})
r2_prioridades.to_excel(writer, sheet_name='R2_Prioridades', index=False)

# SHEET 4: Regra 3 - Temperatura
r3_temperatura = pd.DataFrame({
    'Parâmetro': [
        'Temperatura máxima bateria',
        'Temperatura ideal mínima bateria',
        'Temperatura ideal máxima bateria',
        'Temperatura máxima carregador'
    ],
    'Valor': [45.0, 15.0, 35.0, 60.0],
    'Unidade': ['°C', '°C', '°C', '°C'],
    'Ação se Exceder': [
        'PARAR carregamento imediatamente',
        'Pré-aquecer bateria antes de carregar',
        'REDUZIR potência para 80 kW',
        'Aguardar arrefecimento do carregador'
    ],
    'Potência Ajustada': [0.0, 50.0, 80.0, 0.0]
})
r3_temperatura.to_excel(writer, sheet_name='R3_Temperatura', index=False)

# SHEET 5: Regra 4 - Disponibilidade
r4_disponibilidade = pd.DataFrame({
    'Estado': ['IDLE', 'CHARGING', 'FAULT', 'MAINTENANCE'],
    'Descrição': [
        'Estação disponível para uso',
        'Estação ocupada a carregar',
        'Estação com falha técnica',
        'Estação em manutenção'
    ],
    'Pode Alocar?': ['Sim', 'Não', 'Não', 'Não'],
    'Ação Requerida': [
        'Disponível para alocação',
        'Aguardar fim do carregamento',
        'Reparação técnica necessária',
        'Aguardar fim da manutenção'
    ]
})
r4_disponibilidade.to_excel(writer, sheet_name='R4_Disponibilidade', index=False)

# SHEET 6: Regra 5 - Distância
r5_distancia = pd.DataFrame({
    'Parâmetro': [
        'Latitude Depósito',
        'Longitude Depósito',
        'Consumo por km',
        'Margem de segurança'
    ],
    'Valor': [41.183580, -8.618978, 1.5, 1.2],
    'Unidade': ['°', '°', 'kWh/km', 'multiplicador'],
    'Descrição': [
        'Coordenada GPS do depósito STCP',
        'Coordenada GPS do depósito STCP',
        'Consumo médio de energia por quilómetro',
        '20% de margem para imprevistos'
    ]
})

r5_status = pd.DataFrame({
    'Condição': [
        'Autonomia < Distância × 1.2',
        'Autonomia < Distância × 1.5',
        'Autonomia ≥ Distância × 1.5'
    ],
    'Status': [
        'CRÍTICO - Não chega ao depósito',
        'ALERTA - Margem reduzida',
        'OK - Consegue chegar'
    ],
    'Urgência': [100, 60, 0],
    'Ação': [
        'Carregar IMEDIATAMENTE',
        'Carregar em breve',
        'Sem ação necessária'
    ]
})

# Criar duas tabelas na mesma sheet
r5_distancia.to_excel(writer, sheet_name='R5_Distancia', index=False, startrow=0)
pd.DataFrame(['']).to_excel(writer, sheet_name='R5_Distancia', index=False, header=False, startrow=len(r5_distancia)+2)
r5_status.to_excel(writer, sheet_name='R5_Distancia', index=False, startrow=len(r5_distancia)+4)

# SHEET 7: Regra 6 - Tempo de Carregamento
r6_tempo = pd.DataFrame({
    'Potência (kW)': [150, 120, 80, 50],
    'Tempo para 10% (min)': [14, 17.5, 26.25, 42],
    'Tempo para 20% (min)': [28, 35, 52.5, 84],
    'Tempo para 30% (min)': [42, 52.5, 78.75, 126],
    'Tempo para 50% (min)': [70, 87.5, 131.25, 210],
    'Classificação': [
        'Carregamento Ultra-Rápido',
        'Carregamento Rápido',
        'Carregamento Normal',
        'Carregamento Lento'
    ]
})
r6_tempo.to_excel(writer, sheet_name='R6_Tempo_Carregamento', index=False)

# SHEET 8: Regra 7 - Balanceamento
r7_balanceamento = pd.DataFrame({
    'Parâmetro': [
        'Potência total disponível',
        'Limite da rede elétrica',
        'Número de estações',
        'Potência máxima por estação'
    ],
    'Valor': [450.0, 400.0, 3, 150.0],
    'Unidade': ['kW', 'kW', 'unidades', 'kW']
})

r7_status_rede = pd.DataFrame({
    'Carga Total': [
        '> 400 kW',
        '360-400 kW (90-100%)',
        '280-360 kW (70-90%)',
        '< 280 kW (<70%)'
    ],
    'Status': [
        'SOBRECARGA',
        'ALERTA',
        'CARGA ELEVADA',
        'NORMAL'
    ],
    'Ação': [
        'Reduzir potência para 80% por estação',
        'Reduzir potência para 90% por estação',
        'Monitorizar',
        'Sem ação'
    ],
    'Potência Máxima por Estação': [
        '120 kW',
        '135 kW',
        '150 kW',
        '150 kW'
    ]
})

r7_balanceamento.to_excel(writer, sheet_name='R7_Balanceamento', index=False, startrow=0)
pd.DataFrame(['']).to_excel(writer, sheet_name='R7_Balanceamento', index=False, header=False, startrow=len(r7_balanceamento)+2)
r7_status_rede.to_excel(writer, sheet_name='R7_Balanceamento', index=False, startrow=len(r7_balanceamento)+4)

# SHEET 9: Regra 8 - Saúde da Bateria
r8_saude = pd.DataFrame({
    'Parâmetro': [
        'Ciclos máximos recomendados',
        'Profundidade descarga ideal mínima',
        'Profundidade descarga ideal máxima',
        'Capacidade inicial bateria'
    ],
    'Valor': [3000, 20.0, 80.0, 350.0],
    'Unidade': ['ciclos', '%', '%', 'kWh'],
    'Descrição': [
        'Vida útil esperada da bateria',
        'Não descarregar abaixo deste nível',
        'Não carregar acima deste nível',
        'Capacidade nova da bateria'
    ]
})

r8_recomendacoes = pd.DataFrame({
    'Nível Bateria': [
        '< 20%',
        '20% - 80%',
        '> 80%'
    ],
    'Status': [
        'ALERTA - Descarga profunda',
        'FAIXA IDEAL',
        'Acima do ideal'
    ],
    'Impacto': [
        'Reduz vida útil da bateria',
        'Boa para longevidade',
        'Pode degradar bateria'
    ],
    'Recomendação': [
        'Carregar até 30% (não até 100%)',
        'Carregar até 80%',
        'Não carregar mais'
    ]
})

r8_saude.to_excel(writer, sheet_name='R8_Saude_Bateria', index=False, startrow=0)
pd.DataFrame(['']).to_excel(writer, sheet_name='R8_Saude_Bateria', index=False, header=False, startrow=len(r8_saude)+2)
r8_recomendacoes.to_excel(writer, sheet_name='R8_Saude_Bateria', index=False, startrow=len(r8_saude)+4)

# SHEET 10: Algoritmo de Decisão
algoritmo_decisao = pd.DataFrame({
    'Passo': [1, 2, 3, 4, 5, 6, 7],
    'Ação': [
        'Obter estado atual dos autocarros (bateria, localização, temperatura)',
        'Obter estado atual das estações (disponibilidade, potência, temperatura)',
        'Calcular score de urgência (prioridade + bateria + distância)',
        'Verificar restrições (temperatura, potência, alcance)',
        'Ordenar autocarros por urgência decrescente',
        'Alocar estações disponíveis aos autocarros mais urgentes',
        'Ajustar potência com base em balanceamento e temperatura'
    ],
    'Regras Aplicadas': [
        'Todas',
        'R4',
        'R2, R5',
        'R1, R3, R5',
        'R2',
        'R4',
        'R1, R3, R7'
    ]
})
algoritmo_decisao.to_excel(writer, sheet_name='Algoritmo_Decisao', index=False)

# SHEET 11: Exemplo Prático
exemplo_pratico = pd.DataFrame({
    'Autocarro': ['BUS-001', 'BUS-002', 'BUS-003'],
    'Bateria Atual': [30.0, 70.0, 25.0],
    'Prioridade Rota': ['Alta', 'Normal', 'Crítica'],
    'Distância Depósito (km)': [7.8, 2.5, 6.5],
    'Autonomia (km)': [70.0, 163.3, 58.3],
    'Consegue Chegar?': ['Sim', 'Sim', 'Sim'],
    'Urgência Score': [60, 0, 100],
    'Decisão': [
        'CARREGAR EM BREVE',
        'NÃO NECESSÁRIO',
        'CARREGAR AGORA'
    ],
    'Estação Alocada': ['CS-002', 'Nenhuma', 'CS-001'],
    'Potência (kW)': [120, 0, 150]
})
exemplo_pratico.to_excel(writer, sheet_name='Exemplo_Pratico', index=False)

# SHEET 12: Glossário
glossario = pd.DataFrame({
    'Termo': [
        'kW',
        'kWh',
        'Score de Urgência',
        'Profundidade de Descarga',
        'Ciclo de Carga',
        'Balanceamento de Carga',
        'Autonomia',
        'Margem de Segurança'
    ],
    'Definição': [
        'Quilowatt - Unidade de potência (velocidade de carregamento)',
        'Quilowatt-hora - Unidade de energia (capacidade da bateria)',
        'Valor 0-100 que indica urgência de carregamento',
        'Percentagem da capacidade da bateria utilizada',
        'Uma carga completa seguida de descarga completa',
        'Distribuição equilibrada de potência entre estações',
        'Distância que o autocarro pode percorrer com bateria atual',
        'Percentagem extra de energia para imprevistos'
    ]
})
glossario.to_excel(writer, sheet_name='Glossario', index=False)

# Guardar e fechar
writer.close()

print(f"✓ Excel criado com sucesso: {output_file}")
print("\nConteúdo:")
print("- Resumo das 8 regras")
print("- Detalhes de cada regra")
print("- Algoritmo de decisão")
print("- Exemplo prático")
print("- Glossário de termos")
