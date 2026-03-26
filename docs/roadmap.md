# Roadmap do Sistema Python

## Fase 1. Fundacao

- estrutura do projeto
- caso de uso minimo `save_qso`
- janela PyQt inicial
- testes basicos do fluxo principal

## Fase 2. Persistencia local

- substituir repositorio em memoria
- introduzir banco local
- suportar listagem de QSOs
- preparar migracoes

## Fase 3. Operacao de log

- editar QSO
- apagar QSO
- busca e filtros
- historico por callsign

Estado atual:

- editar QSO basico
- apagar QSO basico
- busca simples por callsign
- filtros rapidos por banda e modo

## Fase 4. Regras do dominio de radioamador

- resolucao DXCC
- resolucao de banda/modo ampliada
- perfis de estacao
- memberships e tabelas auxiliares

Estado atual:

- perfis de estacao e operador
- logbooks multiplos
- contadores iniciais de DXCC, WAZ e WPX por heuristica

## Fase 5. Integracoes

- importacao/exportacao ADIF
- WSJT-X
- fldigi
- sincronizacao com servicos externos

Estado atual:

- importacao/exportacao ADIF
- integracao inicial com WSJT-X / JTDX via UDP
- fila inicial de Club Log com monitor e persistencia de pendencias

## Fase 6. Maturidade

- auditoria
- eventos e fila interna
- testes de integracao
- empacotamento desktop
