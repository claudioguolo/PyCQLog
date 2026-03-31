# PyCQLog

`PyCQLog` is an open source amateur radio logging application built with Python and PyQt.

`PyCQLog` e um aplicativo open source de log para radioamadorismo, desenvolvido em Python e PyQt.

This project is an initiative led by Claudio - PY9MT.

Este projeto e uma iniciativa de Claudio - PY9MT.

## Purpose | Finalidade

`PyCQLog` was created to offer a modern logging application for Linux that is easier to use, easier to maintain, and easier for the community to evolve over time.

O `PyCQLog` foi criado para oferecer um log moderno para Linux, simples de usar no dia a dia, simples de manter e mais acessivel para evolucao colaborativa ao longo do tempo.

The project focuses on three practical goals:

O projeto se concentra em tres objetivos praticos:

- fast daily logging for real station operation
- local-first data ownership with simple files and SQLite
- an architecture that can grow from desktop use to daemon and remote UI operation

- registro rapido de QSOs para uso real em estacao
- controle local dos dados com arquivos simples e SQLite
- uma arquitetura que pode crescer do desktop para daemon e interface remota

## Why It Is Easy To Use | Facilidade de Uso

`PyCQLog` is designed so the operator can start quickly and keep the workflow clear:

O `PyCQLog` foi desenhado para que o operador comece rapido e mantenha um fluxo claro:

- clean manual QSO entry
- recent QSOs and callsign history on the same screen
- quick ADIF import and export
- built-in dashboard for operating visibility
- PT-BR and English interface
- local mode or daemon plus remote UI mode, depending on the station setup

- captura manual de QSO sem excesso de passos
- QSOs recentes e historico do callsign na mesma tela
- importacao e exportacao ADIF de forma direta
- dashboard integrado para acompanhar a operacao
- interface em PT-BR e English
- uso local ou modo daemon com UI remota, conforme a estacao

## Highlights

- manual QSO entry with CRUD
- local SQLite persistence
- multiple logbooks with active log selection
- reusable operator and station profiles
- ADIF import and export
- dashboard with operating statistics
- PT-BR and English interface
- light, dark, and system themes
- WSJT-X and JTDX UDP capture
- realtime Club Log and QRZ.com queue support
- QRZ.com Callbook lookup
- LoTW ADIF export and TQSL signing
- daemon mode with HTTP API
- remote UI support with host, port, and auth code

## Operating Modes | Modos de Operacao

`PyCQLog` can be used in three main ways:

O `PyCQLog` pode ser usado de tres formas principais:

1. Local desktop: the UI uses the local database and integrations on the same machine.
2. Daemon only: a small Linux host or Raspberry Pi keeps UDP capture and online queues running.
3. Remote UI: the desktop UI connects to a daemon running on another host in the local network.

1. Desktop local: a interface usa o banco e as integracoes na mesma maquina.
2. Somente daemon: um host Linux pequeno ou Raspberry Pi mantem a captura UDP e as filas online em execucao.
3. UI remota: a interface desktop se conecta a um daemon executando em outro host da rede local.

## Documentation | Documentacao

- Project docs index: [docs/README.md](docs/README.md)
- Quick start in English: [docs/quick_start_en.md](docs/quick_start_en.md)
- User guide in English: [docs/user_guide_en.md](docs/user_guide_en.md)
- FAQ in English: [docs/faq_en.md](docs/faq_en.md)

## Installation For Development | Instalacao para Desenvolvimento

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -e .[dev]
```

## Running The Application | Como Iniciar

Full local desktop mode:

Modo desktop local completo:

```bash
pycqlog
```

Desktop UI only:

Somente a interface:

```bash
pycqlog --ui
```

Daemon only:

Somente o daemon:

```bash
pycqlog --service
```

Alternative module form:

Forma alternativa via modulo:

```bash
PYTHONPATH=src python3 -m pycqlog.main
```

## Configuration Files | Arquivos de Configuracao

The project now uses separate configuration files:

O projeto agora usa arquivos separados de configuracao:

- UI: `~/.config/pycqlog/pycqlog_ui.conf`
- daemon: `~/.config/pycqlog/pycqlog_daemon.conf`

The desktop UI can edit remote connection settings directly from:

A interface pode editar as configuracoes de conexao remota diretamente em:

`Integracoes > Remotos`

## Debian Package

To build a `.deb` package locally:

Para gerar um pacote `.deb` localmente:

```bash
bash packaging/build_deb.sh
```

The package will be generated under `dist/deb/`.

O pacote sera gerado em `dist/deb/`.

To install it:

Para instalar:

```bash
sudo apt install ./dist/deb/pycqlog_<version>_all.deb
```

## Linux Notes

If Qt fails with the `xcb` plugin, install:

Se o Qt falhar com o plugin `xcb`, instale:

```bash
sudo apt-get install -y \
  libxcb-cursor0 \
  libxcb-icccm4 \
  libxcb-image0 \
  libxcb-keysyms1 \
  libxcb-render-util0
```

## Testing

```bash
pytest
```

## License And Contribution | Licenca e Colaboracao

- License: [MIT](LICENSE)
- Contribution guide: [CONTRIBUTING.md](CONTRIBUTING.md)
- Security policy: [SECURITY.md](SECURITY.md)
