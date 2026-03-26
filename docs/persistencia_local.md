# Persistencia Local

## Objetivo

O `PyCQLog` agora usa persistencia local em SQLite para manter os QSOs entre execucoes da aplicacao.

## Implementacao atual

Repositorio principal:

- [src/pycqlog/infrastructure/repositories.py](../src/pycqlog/infrastructure/repositories.py)

Bootstrap:

- [src/pycqlog/bootstrap.py](../src/pycqlog/bootstrap.py)

## Local do banco

O banco atual e criado automaticamente em um destes caminhos:

```text
~/.local/share/pycqlog/pycqlog.db
```

ou, se configurado pelo usuario:

```text
<diretorio_de_dados_configurado>/pycqlog.db
```

Se esse diretorio nao estiver disponivel, o sistema usa:

```text
./.pycqlog_data/pycqlog.db
```

Tambem e possivel definir manualmente:

```text
PYCQLOG_DATA_DIR=/caminho/desejado
```

## Comportamento atual

- schema criado automaticamente na inicializacao
- tabelas `logbooks`, `station_profiles` e `qsos`
- gravacao de novos QSOs
- leitura dos QSOs mais recentes para a interface desktop
- o diretorio de configuracao e separado do diretorio de dados
- selecao de logbook ativo compartilhada com a interface

## Proximos passos

- migracoes versionadas
- refinamento de migracoes e versao de schema
- indices para busca
