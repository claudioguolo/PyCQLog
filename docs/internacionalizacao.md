# Internacionalizacao

## Objetivo

O `PyCQLog` agora possui uma base de internacionalizacao para permitir crescimento internacional da aplicacao.

## Idiomas atuais

- `pt-BR`
- `en`

## Arquivos principais

- [src/pycqlog/localization.py](../src/pycqlog/localization.py)
- [src/pycqlog/infrastructure/settings.py](../src/pycqlog/infrastructure/settings.py)
- [src/pycqlog/interfaces/desktop/main_window.py](../src/pycqlog/interfaces/desktop/main_window.py)

## Como funciona

- a interface usa chaves de traducao, nao textos fixos
- o idioma escolhido e salvo em `settings.json`
- a aplicacao carrega o idioma salvo na inicializacao
- a troca de idioma pode ser feita pelo menu da aplicacao

## Como adicionar um novo idioma

1. adicionar um novo bloco em `TRANSLATIONS` em [src/pycqlog/localization.py](../src/pycqlog/localization.py)
2. preencher as mesmas chaves existentes em `pt-BR` e `en`
3. reiniciar a aplicacao ou selecionar o idioma, se ele ja estiver disponivel no menu

## Observacao

Essa estrutura foi criada para ser simples agora e facil de expandir depois para catalogos externos, arquivos JSON dedicados ou ferramentas de localizacao mais completas.
