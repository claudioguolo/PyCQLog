# Importacao ADIF

## Objetivo

O `PyCQLog` agora possui importacao inicial de arquivos ADIF para trazer QSOs existentes para o banco local.

## Arquivos principais

- [src/pycqlog/infrastructure/adif.py](../src/pycqlog/infrastructure/adif.py)
- [src/pycqlog/application/use_cases.py](../src/pycqlog/application/use_cases.py)
- [src/pycqlog/interfaces/desktop/main_window.py](../src/pycqlog/interfaces/desktop/main_window.py)

## Fluxo atual

- o usuario abre a acao `Importar ADIF` no menu
- seleciona um arquivo `.adi` ou `.adif`
- o sistema apresenta uma pre-visualizacao antes da gravacao
- o usuario pode filtrar os registros por status no preview
- o usuario pode marcar em lote os registros prontos e limpar a selecao
- o usuario pode desmarcar registros individuais prontos para importacao
- o usuario pode editar `callsign`, `data`, `hora`, `frequencia` e `modo` antes de importar
- o parser le os registros e converte campos principais
- cada registro e persistido pelo caso de uso `save_qso`
- registros duplicados sao ignorados por comparacao basica
- a interface mostra quantos QSOs entraram, quantos foram ignorados e quantos falharam

## Campos suportados na primeira versao

- `CALL`
- `QSO_DATE`
- `TIME_ON`
- `FREQ`
- `MODE`
- `RST_SENT`
- `RST_RCVD`
- `OPERATOR`
- `STATION_CALLSIGN`
- `COMMENT`
- `SUBMODE`
- `NAME`
- `QTH`

## Limitacoes atuais

- deduplicacao baseada em `callsign + data + hora + frequencia + modo`
- sem mapeamento avancado de todos os submodos ADIF
- sem importacao de todos os campos ADIF
- sem acoes avancadas em lote por multiplos criterios alem do status
- sem perfis persistentes de importacao
