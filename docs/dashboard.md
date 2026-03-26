# Dashboard

## Objetivo

O `PyCQLog` agora possui um dashboard operacional com estatisticas e graficos simples para leitura rapida do log.

## Arquivos principais

- [src/pycqlog/application/use_cases.py](../src/pycqlog/application/use_cases.py)
- [src/pycqlog/interfaces/desktop/dashboard_dialog.py](../src/pycqlog/interfaces/desktop/dashboard_dialog.py)
- [src/pycqlog/interfaces/desktop/main_window.py](../src/pycqlog/interfaces/desktop/main_window.py)

## Conteudo atual

- cards com total de QSOs, callsigns unicos, bandas ativas e modos ativos
- cards com contadores de DXCC, WAZ e WPX resolvidos por base local de prefixos
- filtro por periodo no proprio painel
- cores especificas por banda e por modo, configuraveis pelo menu
- opcao para reaproveitar essas cores nas tabelas principais
- filtros rapidos clicaveis por banda e modo no topo da lista principal
- grafico de QSOs por banda
- grafico de QSOs por modo
- grafico de QSOs por dia
- grafico de evolucao mensal
- grafico de distribuicao por hora
- tabela com top callsigns

## Fluxo atual

- o usuario abre `Dashboard` no menu principal
- o sistema consolida os QSOs do logbook ativo
- o usuario pode alternar entre todo o log, ultimos 7 dias, ultimos 30 dias e ultimos 12 meses
- a interface apresenta os indicadores e graficos em uma janela dedicada
- se o dashboard estiver aberto, ele e atualizado apos salvar, importar ou excluir QSOs

## Limitacoes atuais

- os graficos atuais sao desenhados manualmente e ainda nao possuem interacao
- a resolucao de awards ainda e baseada em prefixo, embora mais robusta e conservadora do que a heuristica inicial
- ainda nao ha persistencia de preferencias de visualizacao
