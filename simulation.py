import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from math import radians, cos, sin, asin, sqrt

ARQUIVO_DADOS = 'bin-sensors-ubidots-historical.csv'
CAPACIDADE_LIXEIRA_MM = 950.0 
LIMIAR_COLETA = 70.0  

plt.style.use('ggplot') 

def haversine(lon1, lat1, lon2, lat2):
    """Calcula distância entre dois pontos (Haversine) em km"""
    lon1, lat1, lon2, lat2 = map(radians, [lon1, lat1, lon2, lat2])
    dlon = lon2 - lon1 
    dlat = lat2 - lat1 
    a = sin(dlat/2)**2 + cos(lat1) * cos(lat2) * sin(dlon/2)**2
    c = 2 * asin(sqrt(a)) 
    r = 6371 
    return c * r

def calcular_rota_nn(df_locations):
    """Calcula rota usando Vizinho Mais Próximo (Nearest Neighbor)"""
    if len(df_locations) < 2:
        return 0.0
    
    locations = df_locations.copy()
    atual = locations.iloc[0]
    nao_visitados = locations.iloc[1:].copy()
    distancia_total = 0.0
    
    while not nao_visitados.empty:
        distancias = nao_visitados.apply(
            lambda row: haversine(atual['lon'], atual['lat'], row['lon'], row['lat']), 
            axis=1
        )
        idx_mais_proximo = distancias.idxmin()
        dist_minima = distancias.min()
        
        distancia_total += dist_minima
        atual = nao_visitados.loc[idx_mais_proximo]
        nao_visitados = nao_visitados.drop(idx_mais_proximo)
        
    return distancia_total

def carregar_e_tratar():
    print("--- ENGENHARIA DE DADOS: ETL EM ANDAMENTO ---")
    print("1. Carregando dataset...")
    df = pd.read_csv(ARQUIVO_DADOS, sep=';')
    
    print("2. Tratando geolocalização e timestamps...")
    df['Time'] = pd.to_datetime(df['Time'], utc=True)
    df['Date'] = df['Time'].dt.date 
    
    def parse_geo(geo_str):
        try:
            if isinstance(geo_str, str):
                lat, lon = map(float, geo_str.split(','))
                return lat, lon
        except:
            pass
        return None, None

    geodata = df['Geolocation'].apply(parse_geo)
    df['lat'] = [x[0] for x in geodata]
    df['lon'] = [x[1] for x in geodata]
    df = df.dropna(subset=['lat', 'lon'])
    
    # Calcular % de ocupação
    df['fill_pct'] = (df['Full Level'] / CAPACIDADE_LIXEIRA_MM) * 100
    
    return df

def rodar_simulacao():
    df = carregar_e_tratar()
    
    dias_unicos = sorted(df['Date'].unique())
    print(f"3. Iniciando simulação para {len(dias_unicos)} dias de operação...")
    
    resultados = []
    
    for dia in dias_unicos:
        df_dia_full = df[df['Date'] == dia]
        
        df_estado_dia = df_dia_full.sort_values('Time').groupby('Ubidots Apilabel').last().reset_index()
        
        if len(df_estado_dia) < 10: 
            continue

         # --- CENÁRIO A: Rota Fixa (Visita todos os sensores ativos) ---
        dist_fixa = calcular_rota_nn(df_estado_dia)
        paradas_fixa = len(df_estado_dia)
        
        # --- CENÁRIO B: Rota Otimizada (Apenas > 70%) ---
        df_cheias = df_estado_dia[df_estado_dia['fill_pct'] >= LIMIAR_COLETA]
        
        if len(df_cheias) > 0:
            dist_smart = calcular_rota_nn(df_cheias)
            paradas_smart = len(df_cheias)
        else:
            dist_smart = 0
            paradas_smart = 0
            
        resultados.append({
            'Data': dia,
            'Distancia_Fixa': dist_fixa,
            'Distancia_Smart': dist_smart,
            'Paradas_Fixa': paradas_fixa,
            'Paradas_Smart': paradas_smart
        })
    
    df_res = pd.DataFrame(resultados)
    
    # --- CÁLCULO DE KPIS GERAIS ---
    total_km_fixo = df_res['Distancia_Fixa'].sum()
    total_km_smart = df_res['Distancia_Smart'].sum()
    economia_km = total_km_fixo - total_km_smart
    pct_economia = (economia_km / total_km_fixo) * 100
    
    total_paradas_fixo = df_res['Paradas_Fixa'].sum()
    total_paradas_smart = df_res['Paradas_Smart'].sum()
    paradas_evitadas = total_paradas_fixo - total_paradas_smart
    
    print("\n" + "="*40)
    print("RESULTADOS CONSOLIDADOS (AGO-OUT 2025)")
    print("="*40)
    print(f"Dias analisados: {len(df_res)}")
    print(f"Distância Total (Fixo):  {total_km_fixo:.2f} km")
    print(f"Distância Total (Smart): {total_km_smart:.2f} km")
    print(f"--> ECONOMIA DE ROTA:    {economia_km:.2f} km ({pct_economia:.1f}%)")
    print("-" * 40)
    print(f"Total de Paradas (Fixo): {total_paradas_fixo}")
    print(f"Total de Paradas (Smart):{total_paradas_smart}")
    print(f"--> PARADAS EVITADAS:    {paradas_evitadas} (Redução de {(1 - total_paradas_smart/total_paradas_fixo)*100:.1f}%)")
    print("="*40)

    # --- GERAÇÃO DE GRÁFICOS ---
    print("4. Gerando gráficos para o artigo...")
    
    # Gráfico 1: Comparativo Diário de Distância
    plt.figure(figsize=(12, 6))
    plt.plot(df_res['Data'], df_res['Distancia_Fixa'], label='Rota Fixa (Tradicional)', color='red', alpha=0.7)
    plt.plot(df_res['Data'], df_res['Distancia_Smart'], label='Rota Otimizada (IoT)', color='green', linewidth=2)
    plt.fill_between(df_res['Data'], df_res['Distancia_Smart'], df_res['Distancia_Fixa'], color='green', alpha=0.1, label='Economia Gerada')
    plt.title('Comparativo de Distância Percorrida: Fixo vs Smart')
    plt.ylabel('Distância (km)')
    plt.xlabel('Data')
    plt.legend()
    plt.grid(True)
    plt.savefig('grafico_comparativo_distancia.png')
    print(" -> Gráfico salvo: grafico_comparativo_distancia.png")
    
    # Gráfico 2: Eficiência de Paradas (Barras)
    plt.figure(figsize=(10, 6))
    indices = np.arange(len(df_res))
    width = 0.35
    
    df_set = df_res[(pd.to_datetime(df_res['Data']) >= pd.to_datetime('2025-09-01')) & 
                    (pd.to_datetime(df_res['Data']) <= pd.to_datetime('2025-09-30'))]
    
    plt.bar(df_set['Data'], df_set['Paradas_Fixa'], width=0.4, label='Paradas Totais (Cenário Fixo)', color='gray')
    plt.bar(df_set['Data'], df_set['Paradas_Smart'], width=0.4, label='Paradas Necessárias (Cenário Smart)', color='green')
    
    plt.title('Eficiência Operacional: Paradas Realizadas vs Necessárias (Setembro 2025)')
    plt.ylabel('Número de Coletas')
    plt.xticks(rotation=45)
    plt.legend()
    plt.tight_layout()
    plt.savefig('grafico_eficiencia_paradas.png')
    print(" -> Gráfico salvo: grafico_eficiencia_paradas.png")

if __name__ == "__main__":
    rodar_simulacao()
