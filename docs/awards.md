# Awards

## Objetivo

O `PyCQLog` agora possui uma base local embarcada para resolucao de `DXCC`, `CQ zone` e `WPX`, focada em uso operacional mais serio no dashboard.

## O que mudou

- a contagem deixou de depender apenas de heuristica simples
- a resolucao agora usa uma base local curada de prefixos
- o matching considera o prefixo mais especifico primeiro
- callsigns com barra, como `KH6/PY2ABC` e `PY2ABC/P`, sao tratados de forma mais inteligente
- `WPX` continua sendo derivado do callsign base

## Escopo atual

- resolucao local de entidade e zona por prefixo
- suporte a prefixos comuns das Americas, Europa, Asia, Africa e Oceania
- fallback mais conservador: entidades nao mapeadas nao entram como `DXCC` valido

## Limitacoes atuais

- ainda nao usamos uma base oficial completa como `cty.dat`
- a resolucao continua baseada em prefixo, nao em validacao de callsign real por pais
- awards confirmados ainda nao existem nesta fase

## Impacto pratico

- dashboard mais confiavel para `DXCC`, `WAZ` e `WPX`
- menos inflacao artificial do contador de entidades
- melhor comportamento com operacao portable e prefixo de pais na barra
