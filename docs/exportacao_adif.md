# Exportacao ADIF

## Objetivo

O `PyCQLog` agora permite exportar os QSOs gravados no banco local para um arquivo ADIF.

## Arquivos principais

- [src/pycqlog/infrastructure/adif_export.py](../src/pycqlog/infrastructure/adif_export.py)
- [src/pycqlog/application/use_cases.py](../src/pycqlog/application/use_cases.py)
- [src/pycqlog/interfaces/desktop/main_window.py](../src/pycqlog/interfaces/desktop/main_window.py)

## Fluxo atual

- o usuario abre a acao `Exportar ADIF` no menu
- escolhe filtros opcionais por callsign, periodo, banda e modo
- escolhe o arquivo de destino `.adi` ou `.adif`
- o sistema exporta os QSOs do banco local que correspondem aos filtros
- o diretorio padrao dos logs e usado como ponto inicial do seletor
- o nome sugerido do arquivo usa o prefixo configurado nas preferencias ADIF
- apos exportar, a pasta escolhida passa a ser reutilizada nas proximas importacoes e exportacoes

## Campos exportados

- `CALL`
- `QSO_DATE`
- `TIME_ON`
- `FREQ`
- `BAND`
- `MODE`
- `RST_SENT`
- `RST_RCVD`
- `OPERATOR`
- `STATION_CALLSIGN`
- `COMMENT`
- `APP_PYCQLOG_SOURCE`

## Limitacoes atuais

- ainda nao ha selecao por registros individuais na exportacao
- ainda nao ha exportacao Cabrillo
