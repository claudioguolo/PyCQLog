# Logbooks e Perfis

## Objetivo

O `PyCQLog` agora suporta operacao com multiplos logbooks e perfis reutilizaveis de operador/estacao.

## Arquivos principais

- [src/pycqlog/domain/models.py](../src/pycqlog/domain/models.py)
- [src/pycqlog/infrastructure/repositories.py](../src/pycqlog/infrastructure/repositories.py)
- [src/pycqlog/application/use_cases.py](../src/pycqlog/application/use_cases.py)
- [src/pycqlog/interfaces/desktop/logbooks_dialog.py](../src/pycqlog/interfaces/desktop/logbooks_dialog.py)
- [src/pycqlog/interfaces/desktop/station_profiles_dialog.py](../src/pycqlog/interfaces/desktop/station_profiles_dialog.py)

## Recursos atuais

- selecao de logbook ativo na tela principal
- cadastro e edicao de logbooks
- cadastro e edicao de perfis de operador e estacao
- associacao de perfis padrao a cada logbook
- isolamento dos QSOs por logbook ativo
- importacao e exportacao ADIF respeitando o logbook atual

## Comportamento atual

- o banco SQLite agora possui tabelas para `logbooks`, `station_profiles` e `qsos`
- cada QSO pertence a um logbook
- trocar o logbook ativo recarrega lista, historico e dashboard
- os defaults de operador e estacao do formulario passam a vir do logbook ativo quando houver perfis associados
- o sistema preserva um logbook padrao para compatibilidade com bases ja existentes

## Observacao

- os indicadores de DXCC, WAZ e WPX nesta fase sao iniciais e baseados em heuristica de prefixo, servindo como preparacao arquitetural para uma base de entidades mais completa
