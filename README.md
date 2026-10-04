# Radar Eleitoral 2026 — Coletor V1

Coletor inicial do Radar Eleitoral 2026, preparado para consumir os arquivos oficiais de divulgação de resultados do TSE.

## Fonte oficial

- Base: https://resultados.tse.jus.br
- Configuração: `https://resultados.tse.jus.br/oficial/comum/config/ele-c.json`

O coletor lê o `ele-c.json` para descobrir automaticamente:
- ciclo;
- eleição;
- código do 1º turno;
- código do eventual 2º turno;
- cargos e abrangências.

## Arquivos usados

- EA11: configuração da eleição (`ele-c.json`)
- EA14: acompanhamento Brasil
- EA15: acompanhamento por UF
- EA20: resultado unificado
- EA10: resultado de eleitos, quando disponibilizado

O Presidente é tratado pela totalização nacional do EA20. O EA10 é usado para os cargos para os quais o TSE o disponibiliza.

## Execução local

```bash
python collector.py
```

Ou:

```bash
python collector.py --turno auto
python collector.py --turno 1
python collector.py --turno 2
```

Os dados são gravados em `data/`.

## Variáveis opcionais

```text
TSE_BASE_URL=https://resultados.tse.jus.br
TSE_ENV=oficial
REQUEST_TIMEOUT=20
```

## Estratégia de atualização

O coletor usa EA14/EA15 para identificar mudanças e consulta EA20 somente quando necessário. Também mantém ETag/Last-Modified quando disponíveis.

O GitHub Actions da V1 está preparado para execução periódica. Para acompanhamento realmente contínuo, o painel deverá atualizar sua leitura independentemente do intervalo do workflow.

## Observação

Não declarar vencedor por heurística quando houver informação oficial do TSE. O sistema deve distinguir:
- EM APURAÇÃO
- TOTALIZAÇÃO FINAL
- ELEITO OFICIAL
- SEGUNDO TURNO
- SEM ATRIBUIÇÃO DE ELEITO
