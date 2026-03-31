# Inicio Rapido - pt-BR

## Objetivo

Este guia coloca o `PyCQLog` em operacao rapidamente, com foco em simplicidade.

O projeto foi pensado para que voce consiga:

- abrir a interface e registrar um QSO em poucos minutos
- importar ou exportar ADIF sem passos excessivos
- integrar com JTDX ou WSJT-X
- evoluir depois para um daemon remoto, se a estacao exigir

## Formas de uso

O `PyCQLog` pode ser usado de tres formas:

1. Desktop local, quando tudo roda na mesma maquina.
2. Somente daemon, para servidor pequeno ou Raspberry Pi.
3. UI remota, quando a interface acessa um daemon em outro host.

## Em poucos minutos

1. Crie e ative um ambiente virtual:

```bash
python3 -m venv .venv
source .venv/bin/activate
```

2. Instale a aplicacao:

```bash
pip install -e .
```

3. Inicie no modo desejado:

Desktop local:

```bash
pycqlog
```

Somente daemon:

```bash
pycqlog --service
```

Somente interface:

```bash
pycqlog --ui
```

Se voce tiver um pacote `.deb`, tambem pode instalar assim:

```bash
sudo apt install ./pycqlog_<versao>_all.deb
```

## Primeira configuracao

Revise estes pontos:

- `Configuracoes > Idioma`
- `Configuracoes > Tema`
- `Configuracoes > Diretorios`
- `Configuracoes > ADIF`
- `Integracoes > Remotos`

Se voce estiver usando a interface contra um daemon remoto, ajuste em `Integracoes > Remotos`:

- IP ou host do daemon
- porta
- codigo de autenticacao

## Primeiro QSO manual

Na janela principal:

1. informe `callsign`
2. ajuste `data` e `hora`
3. informe `frequencia`
4. escolha `modo`
5. clique em `Salvar QSO`

O sistema vai:

- validar os campos principais
- calcular a banda pela frequencia quando possivel
- gravar o QSO no logbook ativo

## Importar ADIF

Menu:

```text
Configuracoes > ADIF > Importar ADIF
```

Fluxo:

1. escolha um arquivo `.adi` ou `.adif`
2. revise o preview
3. marque ou desmarque registros
4. edite os campos necessarios
5. confirme a importacao

## Exportar ADIF

Menu:

```text
Configuracoes > ADIF > Exportar ADIF
```

Voce pode exportar:

- todo o logbook ativo
- por callsign
- por periodo
- por banda
- por modo

## Integracao com JTDX ou WSJT-X

Menu:

```text
Integracoes > Remotos
```

Para captura local:

1. habilite o listener `UDP`
2. defina `host` e `porta`
3. configure o `JTDX` ou `WSJT-X` para enviar `Logged ADIF`
4. acompanhe em `Integracoes > Monitor da Integracao`

## Modo remoto

Arquivos usados:

- UI: `~/.config/pycqlog/pycqlog_ui.conf`
- daemon: `~/.config/pycqlog/pycqlog_daemon.conf`

Exemplo:

- no servidor, rode `pycqlog --service`
- no cliente, configure `service_remote_enabled = true`
- abra a UI com `pycqlog --ui`

## Onde procurar ajuda

- guia completo: [guia_do_usuario_pt-BR.md](guia_do_usuario_pt-BR.md)
- FAQ: [faq_pt-BR.md](faq_pt-BR.md)
- integracoes: [integracoes.md](integracoes.md)
- importacao ADIF: [importacao_adif.md](importacao_adif.md)
