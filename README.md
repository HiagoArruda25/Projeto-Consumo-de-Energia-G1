# ⚡ Consumo de Energia Elétrica no Brasil (2015–2024)

**Projeto:** Avaliação G1 — Tema 14  
**Disciplina:** Linguagem de Programação — Análise e Visualização de Dados com Python  
**Aluno:** Hiago da Silva Arruda  
**Professor:** Alexandre Neves Louzada

## Links
- 📊 Dashboard (Streamlit): `https://haprjconsumoenergia.streamlit.app/`
- 🌐 Página do projeto (GitHub Pages): `https://hiagoarruda25.github.io/Projeto-Consumo-de-Energia-G1/`

## Problema
Investigar padrões de consumo de energia elétrica no Brasil: quais estados e setores consomem mais, como o consumo evolui, se há sazonalidade, se a temperatura se relaciona com o consumo e onde estão os riscos de demanda.

## Base de dados
`dados/simulacao_consumo_energia_brasil.csv` — dataset **simulado** (4.440 linhas × 14 colunas, 20 estados, 5 setores, 2015–2024).

## Tecnologias
Python · Pandas · NumPy · Plotly · Matplotlib · Seaborn · Streamlit · GitHub

## Funcionalidades
- **Intermediárias:** filtros múltiplos (ano, mês, região, estado, setor, nível de demanda), KPIs dinâmicos, análise temporal, dashboard em seções (abas), visualizações comparativas, análise geográfica, upload de CSV.
- **Avançadas:** correlação estatística (Pearson/Spearman + matriz), séries temporais avançadas (média móvel de 12 meses e variação anual), mapa interativo (Plotly).

## Principais resultados
- O consumo anual oscila (menor valor em 2020) e o consumo é bem equilibrado entre os setores.
- Não há sazonalidade estável nem relação entre temperatura e consumo (Pearson ≈ 0) — esperado em dados simulados.
- ⚠️ A base tem número de registros desigual por estado (ex.: RJ 480, AM 120), então o ranking por *total* favorece quem tem mais linhas; por isso o dashboard também mostra a *média por registro*.

## Estrutura
```
projeto-consumo-energia/
├── app.py                  # dashboard Streamlit
├── requirements.txt
├── README.md
├── index.html              # página do GitHub Pages
├── dados/                  # CSV da base
├── database/               # (reservado para SQLite)
├── notebooks/analise_consumo_energia.ipynb
└── imagens/                # gráficos usados na página
```

## Como executar
```bash
pip install -r requirements.txt
streamlit run app.py
```
