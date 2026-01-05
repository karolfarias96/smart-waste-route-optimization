# Smart Waste Route Optimization 🚛♻️

> **Título:** Gestão Inteligente da Coleta de Resíduos: Avaliação do Impacto da Otimização de Rotas

Este repositório contém a implementação dos algoritmos e simulações utilizados no artigo acadêmico sobre otimização logística de resíduos sólidos urbanos. O projeto utiliza dados reais de sensores IoT (Eurobodalla, Austrália) para comparar a eficiência de rotas fixas versus rotas dinâmicas baseadas em demanda.

## 📊 Resultados Principais

A simulação, abrangendo o período de Agosto a Outubro de 2025, demonstrou que a migração para um modelo *Data-Driven* gera:

| Indicador | Modelo Tradicional | Modelo Otimizado (IoT) | Impacto |
| :--- | :---: | :---: | :---: |
| **Distância Percorrida** | 3.891 km | 2.107 km | **🔻 45,8% de Economia** |
| **Paradas Realizadas** | 2.361 | 163 | **🔻 93,1% de Redução** |

## 🛠️ Tecnologias Utilizadas

* **Linguagem:** Python 3.x
* **Análise de Dados:** Pandas, NumPy
* **Visualização:** Matplotlib
* **Geoprocessamento:** Fórmula de Haversine (Cálculo de distâncias geodésicas)
* **Algoritmo:** Heurística do Vizinho Mais Próximo (Nearest Neighbor) aplicado ao VRP (Vehicle Routing Problem).

## 📂 Estrutura do Projeto

* `simulation.py`: Script principal contendo o ETL dos dados, o motor de simulação e a geração dos gráficos.
* `bin-sensors-ubidots-historical.csv`: Dataset histórico contendo telemetria dos níveis de preenchimento e geolocalização.
* `grafico_comparativo_distancia.png`: Visualização da série temporal de quilometragem.
* `grafico_eficiencia_paradas.png`: Visualização comparativa de paradas operacionais.


## 📈 Metodologia

O estudo compara dois cenários:
1.  **Cenário Baseline (Rota Fixa):** O veículo visita todas as lixeiras ativas diariamente, simulando a operação atual da maioria das cidades.
2.  **Cenário Smart (Rota Dinâmica):** O veículo visita apenas lixeiras com nível de preenchimento > 70%, utilizando dados de sensores para filtrar a demanda.
