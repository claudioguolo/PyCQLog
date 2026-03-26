# Arquitetura do PyCQLog

## Visao geral

O `PyCQLog` esta sendo construido como uma aplicacao desktop em Python com PyQt6, organizada em camadas para separar interface, regras de negocio e infraestrutura.

Estrutura atual:

```text
src/pycqlog/
  application/
  domain/
  infrastructure/
  interfaces/
```

## Camadas

### `domain/`

Contem o nucleo de negocio.

Responsabilidades atuais:

- entidades `QsoDraft`, `Qso`, `Logbook` e `StationProfile`
- normalizacao de dados
- enriquecimento de banda
- validacao de QSO
- heuristicas iniciais para DXCC, WAZ e WPX

Arquivos principais:

- [src/pycqlog/domain/models.py](../src/pycqlog/domain/models.py)
- [src/pycqlog/domain/services.py](../src/pycqlog/domain/services.py)

### `application/`

Contem os contratos de entrada/saida e os casos de uso.

Responsabilidades atuais:

- DTO `SaveQsoCommand`
- DTO `SaveQsoResult`
- caso de uso `SaveQsoUseCase`
- casos de uso para logbooks, perfis e dashboard por logbook ativo

Arquivos principais:

- [src/pycqlog/application/dto.py](../src/pycqlog/application/dto.py)
- [src/pycqlog/application/use_cases.py](../src/pycqlog/application/use_cases.py)

### `infrastructure/`

Contem implementacoes tecnicas das portas do sistema.

Responsabilidades atuais:

- repositorio SQLite com tabelas de logbooks, perfis e QSOs
- selecao de logbook ativo no repositorio compartilhado

Arquivo principal:

- [src/pycqlog/infrastructure/repositories.py](../src/pycqlog/infrastructure/repositories.py)

### `interfaces/`

Contem as formas de interacao com o sistema.

Responsabilidades atuais:

- bootstrap da aplicacao desktop
- janela principal em PyQt6
- dialogos de gerenciamento de logbooks e perfis

Arquivos principais:

- [src/pycqlog/interfaces/desktop/app.py](../src/pycqlog/interfaces/desktop/app.py)
- [src/pycqlog/interfaces/desktop/main_window.py](../src/pycqlog/interfaces/desktop/main_window.py)

## Fluxo principal

O fluxo principal atual e:

1. a interface coleta os dados do formulario
2. o logbook ativo define o contexto operacional da gravacao
3. a interface monta um `SaveQsoCommand`
4. o caso de uso normaliza os dados
5. o caso de uso enriquece o QSO com banda derivada
6. o caso de uso valida o draft
7. o repositorio persiste o QSO no logbook ativo
8. a interface recebe o resultado e atualiza o estado visual

## Direcao arquitetural

As proximas evolucoes devem manter estas regras:

- a interface PyQt nao deve conter regra de negocio
- integracoes externas devem entrar por adaptadores
- persistencia real deve substituir o repositorio em memoria sem alterar o fluxo da UI
- novos casos de uso devem ser adicionados em `application/use_cases.py` ou em modulos equivalentes
