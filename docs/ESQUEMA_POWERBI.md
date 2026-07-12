# Esquema do Power BI — Fábrica (4 páginas)

Este documento é o plano de construção do ficheiro `.pbix`. Cada página
corresponde a um departamento e à reunião técnica desse departamento.
Todas as fontes de dados referidas já existem como views MySQL do projeto
(`scripts/sql_view/`) — o Power BI deve ligar-se sempre às views (`vw_*`),
nunca às tabelas `*_processed` diretamente, para herdar automaticamente a
janela móvel de 52 semanas.

---

## 0. Estrutura geral do ficheiro

**Páginas:**
1. Visão Geral (opcional, mas recomendo) — um "cockpit" cruzado
2. Produção
3. Controlo da Qualidade
4. Manutenção
5. Asseguração da Qualidade

**Ligação aos dados:** Import (não DirectQuery) — os dados atualizam-se
uma vez por turno/dia via MySQL, não precisam de tempo real ao segundo, e
Import dá muito melhor performance nos visuais.

**Filtros comuns (sincronizados entre páginas via "Sync slicers"):**
- Intervalo de datas
- Processo (Injection Molding / Blow Molding / Screen Printing / Hot Foil Stamping)
- Máquina

**Convenção de cor** (usar em todo o ficheiro, não só numa página):
- Verde: dentro da meta (OEE ≥ 0,85; Cpk ≥ 1,33; CAPA dentro do prazo)
- Amarelo: zona de atenção (OEE 0,70–0,85; Cpk 1,00–1,33)
- Vermelho: fora da meta (OEE < 0,70; Cpk < 1,00; CAPA vencida)

**Cuidado técnico importante:** `Cpk`, `Cp`, `XBarUCL/LCL` e
`RangeRUCL/LCL` nas views de CQ são valores **já calculados por grupo**
(Característica × Máquina × Molde) e repetidos em todas as linhas desse
grupo — não são um valor por linha único. Se arrastares `Cpk` para um
cartão e o Power BI aplicar SUM ou AVERAGE sobre milhares de linhas, o
resultado sai errado (está a somar/promediar o mesmo número repetido
milhares de vezes, o que por acaso dá o valor certo *só* se todos os
grupos tiverem o mesmo número de linhas — não é o caso aqui). A forma
correta é criar uma medida DAX que primeiro reduz para uma linha por
grupo:

```dax
Cpk Médio (correto) =
AVERAGEX(
    SUMMARIZE('fact_cap_inspection_variable_cq', 
        'fact_cap_inspection_variable_cq'[Characteristic],
        'fact_cap_inspection_variable_cq'[MachineId],
        'fact_cap_inspection_variable_cq'[MoldId],
        "CpkGrupo", AVERAGE('fact_cap_inspection_variable_cq'[Cpk])),
    [CpkGrupo]
)
```

O mesmo cuidado aplica-se a `XBarUCL`/`XBarLCL`/`RangeRUCL`/`RangeRLCL`.

---

## 1. Página "Visão Geral" (cockpit cruzado)

Uma página só com os números que interessam a todos os departamentos ao
mesmo tempo — útil para abrir uma reunião de direção ou para quem só tem
2 minutos.

| Cartão | Fonte |
|---|---|
| OEE global (última semana) | `vw_fact_production_*` |
| FPY global | `vw_fact_*_disposition_lot_cq_52w` |
| MTBF médio da fábrica | `vw_fact_downtime_unplanned_52w` |
| Nº reclamações (mês atual) | `vw_fact_customer_complaints_52w` |
| Nº CAPAs vencidas | `vw_fact_capa_52w` |
| Máquina de maior risco hoje | `ml_predictions_predictive_maintenance` |

Cada cartão tem um link de drill-through para a página do departamento
correspondente (botão "Ver detalhe").

---

## 2. Página "Produção"

**Reunião a que serve:** follow-up diário/semanal de produção, com
supervisores de turno e o responsável de produção.

### Cartões no topo
- OEE global, Disponibilidade, Performance, Qualidade (última semana)
- % Cumprimento do Plano (`ProducedQty` real vs. `PlannedQty`)
- Produção prevista para a próxima semana (`ml_predictions_production_forecast`)

### Visuais
1. **Tendência semanal de OEE por processo** (linha) — `vw_fact_production_*`, uma série por processo
2. **OEE por máquina** (barras, ordenado do pior para o melhor) — mostra imediatamente onde focar
3. **Produção Planejada vs. Real** (combo de barras/linha, semanal) — `vw_fact_production_plan_52w` + `vw_fact_production_*`
4. **Pareto de paradas NÃO planejadas** (o mais importante desta página) — `vw_fact_downtime_unplanned_52w`
5. **Pareto de paradas planejadas** (separado, nunca junto com o de cima — ver nota abaixo)
6. **As 6 grandes perdas** (waterfall ou barras horizontais): downtime não planejado, setup, perda de velocidade, perda de qualidade
7. **OEE por turno** (barras) — mostra se o turno 3 está mesmo a sofrer mais, como o histórico sugere
8. **Scrap % por máquina/molde** — tabela ou barras, vindo do modelo de scrap (`ml_predictions_scrap_rate` + variáveis de importância)

> **Porque o Pareto de paradas está separado em dois:** juntar paradas
> planeadas e não planeadas no mesmo gráfico esconde os problemas reais —
> uma troca de molde ou a pausa do turno 3 aparecem sempre no topo só
> porque acontecem todos os dias, por desenho. O gráfico que interessa
> à reunião de produção é o das paradas NÃO planeadas.

### O que discutir na reunião
- Cumprimos o plano esta semana? Se não, porquê (ver Pareto)?
- Quais são as 3 maiores causas de paragem não planeada esta semana, e o que já foi feito?
- Que máquina está com o OEE mais baixo, e há quanto tempo?
- A previsão de produção da próxima semana bate com a capacidade disponível?

---

## 3. Página "Controlo da Qualidade"

**Reunião a que serve:** reunião semanal de qualidade, com o laboratório
e o responsável de qualidade de processo.

### Cartões no topo
- FPY (First Pass Yield) global e por família (tampa/frasco/tinta)
- Nº de lotes inspecionados
- Nº de lotes aprovados / reprovados
- PPM de defeitos (produção) — `06_kpi_scorecard`
- Cpk médio (usar a medida DAX corrigida, secção 0)

### Visuais
1. **FPY por família de produto** (barras) — `vw_fact_*_disposition_lot_cq_52w`
2. **Top 10 defeitos** (Pareto) — soma de `DefectsFound` por característica, das 3 tabelas de atributo
3. **Heatmap de Cpk** (máquina × característica) — usar a medida corrigida, não a coluna crua
4. **Carta de Controlo X̄-R** — visual de linha com `XBar`, `XBarUCL`, `XBarCL`, `XBarLCL`; slicer para escolher máquina + característica (útil ter isto como página de drill-through, não fixo)
5. **Tendência mensal dos principais defeitos** — linha, top 3 características
6. **Lotes de risco elevado** (tabela) — `ml_predictions_lot_quality`, ordenado por `PredictedRejectionRisk` decrescente — é a lista prática de "que lote inspecionar com mais atenção esta semana"

### O que discutir na reunião
- Alguma característica saiu de controlo esta semana (pontos fora dos limites X̄-R)?
- Que máquina/molde tem o Cpk mais baixo, e o que está a ser feito?
- Os defeitos do Top 10 estão a subir ou a descer face ao mês passado?
- Que lotes o modelo sinalizou como risco elevado — foram inspecionados com atenção redobrada?

---

## 4. Página "Manutenção"

**Reunião a que serve:** reunião diária de manutenção (dispatch de
técnicos) e reunião semanal de fiabilidade.

### Cartões no topo
- MTBF médio da fábrica
- MTTR médio da fábrica
- % paradas planejadas vs. não planejadas (indicador de maturidade — quanto mais planeada, melhor)
- Nº de avarias esta semana

### Visuais
1. **MTBF por máquina** (barras, pior para melhor) — `vw_fact_downtime_unplanned_52w` + `vw_fact_production_*`
2. **MTTR por máquina** (barras)
3. **Pareto de causas de paragem NÃO planeada** (o mesmo da página de Produção, mas aqui com detalhe por equipa de manutenção responsável)
4. **Ranking de risco de avaria HOJE** (tabela, o visual mais acionável desta página) — `ml_predictions_predictive_maintenance`, ordenado por `PredictedFailureRiskToday` — é literalmente a lista para decidir a que máquina mandar um técnico primeiro
5. **Tempo de Setup médio** por processo/máquina
6. **Downtime total por processo** (planeado + não planeado, barras empilhadas)

### O que discutir na reunião
- Que máquina o modelo aponta como maior risco hoje — já foi verificada?
- Quais as causas de avaria mais frequentes esta semana, e há uma causa raiz comum?
- O MTBF de alguma máquina está a piorar face às semanas anteriores?
- A manutenção preventiva planeada está a ser cumprida no prazo?

---

## 5. Página "Asseguração da Qualidade"

**Reunião a que serve:** reunião mensal de QA / revisão de fornecedores e
clientes, com o responsável de QA e compras.

### Cartões no topo
- Nº de reclamações (mês atual)
- CPMU (reclamações por milhão de unidades expedidas)
- Índice de aprovação médio de fornecedores
- Nº de CAPAs vencidas

### Visuais — Clientes
1. **Reclamações por cliente** (barras) — `vw_fact_customer_complaints_52w`
2. **Reclamações por tipo de defeito** (Pareto)
3. **Reclamações por família de produto**
4. **Tendência mensal de reclamações** (linha)
5. **CPMU ao longo do tempo** (linha)

### Visuais — Fornecedores
6. **Matéria-prima rejeitada por tipo de material** (barras) — `vw_fact_raw_material_lot_disposition_52w`
7. **Índice de aprovação por fornecedor** (barras, ordenado do pior para o melhor) — `vw_fact_raw_material_lot_disposition_52w`
8. **Tempo médio de resposta por fornecedor** — `vw_fact_supplier_complaints_52w`

### Visuais — NC/CAPA
9. **NC Interna vs. Externa** (donut)
10. **NC por processo e por área** (barras)
11. **Status de CAPA** (aberta/fechada/vencida — donut ou barras)
12. **Tabela de CAPAs vencidas** — com responsável e dias de atraso, ordenado por mais atrasado primeiro (o visual mais acionável desta página)
13. **Tempo médio de encerramento de CAPA por severidade** (barras)

### O que discutir na reunião
- Que cliente ou tipo de defeito domina as reclamações este mês?
- Que fornecedor tem o pior índice de aprovação — vale a pena uma reunião de negócio com ele?
- Quantas CAPAs estão vencidas, e quem são os responsáveis?
- As NC internas estão a aumentar (sinal de deriva de processo) ou a diminuir?

---

## Notas finais de construção

- **Drill-through**: da página "Visão Geral" para cada página de
  departamento; da página de Qualidade para a Carta de Controlo
  detalhada (por característica); da página de Manutenção/QA para as
  tabelas de detalhe (lista de avarias, lista de CAPAs).
- **Bookmarks**: útil ter um bookmark que alterna entre "ver paradas
  planeadas" e "ver paradas não planeadas" nas páginas de Produção e
  Manutenção, em vez de dois gráficos fixos lado a lado, se o espaço for
  apertado.
- **Atualização**: agendar o refresh do Power BI para correr depois do
  turno da noite (ex: 06:15), para que a reunião das 08:00 já tenha os
  dados do dia anterior completos.
