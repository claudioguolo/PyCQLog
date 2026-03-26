# Guia do Usuario - pt-BR

## Objetivo

Este guia foi escrito para quem vai usar o `PyCQLog` no dia a dia. Ele cobre instalacao, configuracao inicial, operacao basica, importacao e exportacao de logs, dashboard e integracoes.

## O que o PyCQLog faz hoje

O `PyCQLog` e uma aplicacao desktop para radioamadorismo com foco em operacao local e controle dos dados pelo proprio operador.

Recursos principais:

- registro manual de QSO
- edicao e exclusao de QSOs
- busca por callsign
- historico por callsign
- multiplos logbooks
- perfis de operador e estacao
- importacao ADIF
- exportacao ADIF
- dashboard operacional
- integracao inicial com `WSJT-X / JTDX`
- fila configuravel para `Club Log`
- interface em `pt-BR` e `en`

## Requisitos

- Linux com ambiente grafico
- Python `3.11` ou superior
- `PyQt6`

Se o Qt falhar ao abrir a interface por causa do plugin `xcb`, instale:

```bash
sudo apt-get install -y \
  libxcb-cursor0 \
  libxcb-icccm4 \
  libxcb-image0 \
  libxcb-keysyms1 \
  libxcb-render-util0
```

## Instalacao para uso local

Dentro da pasta do projeto:

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -e .
```

## Como abrir a aplicacao

Forma recomendada:

```bash
./pycqlog
```

Alternativa:

```bash
PYTHONPATH=src python3 -m pycqlog.main
```

## Primeira abertura

Ao abrir a aplicacao pela primeira vez, revise estes pontos:

1. idioma da interface
2. tema visual
3. diretorio de dados
4. diretorio padrao dos logs
5. logbook ativo

## Estrutura principal da janela

A janela principal e composta por:

- formulario manual de QSO
- selecao do logbook ativo
- lista de QSOs recentes
- filtros rapidos por banda e modo
- painel de historico por callsign
- barra de menus para configuracoes, dashboard e ajuda

## Logbooks

`Logbook` e o contexto principal de operacao. Ele pode representar:

- log principal
- contest
- portable
- expedicao
- estacao secundaria

### Como trocar o logbook ativo

Na parte superior da janela principal existe o seletor de logbook ativo.

Quando o logbook muda:

- a lista de QSOs e recarregada
- o historico acompanha o logbook atual
- o dashboard passa a refletir esse logbook
- os defaults de operador e estacao podem mudar

### Como gerenciar logbooks

Menu:

```text
Configuracoes > Logbooks
```

No dialogo de logbooks voce pode:

- criar um novo logbook
- editar nome e descricao
- associar perfil de operador
- associar perfil de estacao
- excluir um logbook

## Perfis de operador e estacao

Os perfis servem para reutilizar dados operacionais.

### Dados suportados

- nome do perfil
- tipo
- callsign
- QTH
- locator
- potencia
- antena
- notas

### Onde gerenciar

Menu:

```text
Configuracoes > Perfis
```

### Para que servem

- preencher defaults de operador e estacao
- padronizar informacoes entre logbooks
- evitar digitacao repetitiva

## Registro manual de QSO

No formulario principal voce pode informar:

- callsign
- data
- hora
- frequencia em MHz
- modo
- RST enviado
- RST recebido
- operador
- estacao
- notas

### Como salvar

1. preencha os campos essenciais
2. clique em `Salvar QSO`

O sistema:

- normaliza o callsign
- normaliza o modo
- tenta resolver a banda pela frequencia
- valida os campos obrigatorios
- salva no logbook ativo

### Como editar um QSO

1. selecione o QSO na tabela
2. clique em `Editar Selecionado`
3. altere os campos
4. clique em `Atualizar QSO`

### Como excluir um QSO

1. selecione o QSO na tabela
2. clique em `Excluir Selecionado`
3. confirme a exclusao

## Busca e filtros

### Busca por callsign

Use o campo de busca acima da tabela principal.

### Filtros rapidos

Acima da tabela existem filtros clicaveis por:

- banda
- modo

Voce pode combinar filtros e limpar tudo em `Limpar filtros`.

## Historico por callsign

Ao digitar ou selecionar um callsign, o painel lateral mostra contatos anteriores com esse callsign dentro do logbook ativo.

O historico ajuda a consultar:

- data
- hora
- banda
- modo
- RST

## Dashboard

Menu:

```text
Dashboard > Abrir Dashboard
```

O dashboard mostra indicadores do logbook ativo.
Os contadores de awards agora usam uma base local curada de prefixos, com tratamento melhor para chamadas com barra, embora ainda nao sejam uma base oficial completa.

### Indicadores atuais

- total de QSOs
- callsigns unicos
- bandas ativas
- modos ativos
- DXCC por base local de prefixos
- CQ zones
- WPX prefixes

### Graficos atuais

- QSOs por banda
- QSOs por modo
- QSOs por dia
- evolucao mensal
- QSOs por hora
- top callsigns

### Filtro de periodo

Voce pode alternar entre:

- todo o log
- ultimos 7 dias
- ultimos 30 dias
- ultimos 12 meses

## Idioma e tema

### Idioma

Menu:

```text
Configuracoes > Idioma
```

Idiomas atuais:

- `pt-BR`
- `en`

### Tema

Menu:

```text
Configuracoes > Tema
```

Modos disponiveis:

- `system`
- `light`
- `dark`

## Diretorios

Menu:

```text
Configuracoes > Diretorios
```

### Diretorio de dados

Usado para:

- banco SQLite
- dados locais da aplicacao

### Diretorio padrao dos logs

Usado como base para:

- importacao ADIF
- exportacao ADIF

## Preferencias ADIF

Menu:

```text
Configuracoes > ADIF > Preferencias ADIF
```

Voce pode definir:

- callsign padrao do operador
- callsign padrao da estacao
- prefixo padrao do arquivo de exportacao

## Importacao ADIF

Menu:

```text
Configuracoes > ADIF > Importar ADIF
```

### Fluxo

1. selecione o arquivo `.adi` ou `.adif`
2. revise a pre-visualizacao
3. filtre por status se quiser
4. marque ou desmarque registros
5. edite campos essenciais, se necessario
6. confirme a importacao

### O preview mostra

- total de registros
- prontos
- ignorados
- falhas

### Edicoes permitidas no preview

- callsign
- data
- hora
- frequencia
- modo

## Exportacao ADIF

Menu:

```text
Configuracoes > ADIF > Exportar ADIF
```

### Filtros disponiveis

- callsign
- data inicial
- data final
- banda
- modo

O arquivo exportado usa o prefixo configurado nas preferencias ADIF.

## Integracao com WSJT-X / JTDX

Menu:

```text
Configuracoes > Integracoes > JTDX / Club Log
```

### O que existe hoje

- listener UDP para `Logged ADIF`
- gravacao automatica do QSO no logbook ativo
- fila de upload para Club Log
- controle de autoenvio para QSOs recebidos por UDP e QSOs salvos manualmente

### Configuracoes principais

- ativar captura via UDP
- host local
- porta UDP

### Dica de uso

Configure no `WSJT-X / JTDX` a mesma porta usada no `PyCQLog`.

## Integracao com Club Log

No mesmo dialogo de integracoes voce pode configurar:

- email
- app password
- callsign principal
- API key
- endpoint
- intervalo minimo entre envios

### Observacoes

- o envio e assíncrono
- uploads pendentes ficam em fila local
- se a aplicacao for fechada, a fila pendente pode ser retomada depois

## Monitor da integracao

Menu:

```text
Configuracoes > Integracoes > Monitor
```

O monitor mostra:

- estado do listener UDP
- estado do Club Log
- pacotes recebidos
- QSOs salvos
- uploads concluidos
- falhas
- pendentes
- historico de eventos

### Acoes disponiveis

- `Teste UDP`
- `Teste Club Log`
- `Reenfileirar pendentes`
- `Limpar historico`

## Onde os dados ficam gravados

Por padrao:

- configuracao: `~/.config/pycqlog`
- dados: `~/.local/share/pycqlog`

Se configurado pelo usuario, os caminhos podem mudar.

## Problemas comuns

### A interface nao abre

Verifique:

- se o `PyQt6` foi instalado
- se as bibliotecas `xcb` do Qt estao presentes

### O QSO do JTDX nao entra automaticamente

Verifique:

- se a captura UDP esta habilitada
- se host e porta batem com o software externo
- se o monitor de integracao mostra recebimento de pacote

### O Club Log nao envia

Verifique:

- email
- app password
- callsign principal
- API key
- conectividade de rede
- endpoint configurado

### O dashboard parece vazio

Verifique:

- se o logbook ativo e o esperado
- se o filtro de periodo esta restringindo demais os dados

## Boas praticas de uso

- separe operacoes por logbook
- use perfis para padronizar operador e estacao
- confira o logbook ativo antes de registrar QSOs
- revise importacoes ADIF antes de confirmar
- acompanhe o monitor quando usar integracoes

## Resumo rapido

Se voce quiser usar o sistema com o minimo de passos:

1. abra o `PyCQLog`
2. crie ou escolha o logbook certo
3. configure idioma, tema e diretorios
4. ajuste perfis e defaults ADIF
5. registre manualmente ou importe ADIF
6. abra o dashboard para acompanhar o log
7. se usar digital, habilite a integracao com `WSJT-X / JTDX`
