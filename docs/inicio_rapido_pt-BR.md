# Inicio Rapido - pt-BR

## Objetivo

Este guia foi feito para colocar o `PyCQLog` em operacao em poucos minutos.

## Em 5 minutos

1. Crie e ative um ambiente virtual:

```bash
python3 -m venv .venv
source .venv/bin/activate
```

2. Instale a aplicacao:

```bash
pip install -e .
```

3. Abra o sistema:

```bash
./pycqlog
```

Se voce tiver um pacote `.deb`, tambem pode instalar assim:

```bash
sudo apt install ./pycqlog_<versao>_all.deb
```

4. Revise estas configuracoes:

- `Configuracoes > Idioma`
- `Configuracoes > Tema`
- `Configuracoes > Diretorios`
- `Configuracoes > ADIF`

5. Crie ou selecione um `Logbook`.

6. Registre um QSO manual ou importe um arquivo `ADIF`.

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

## Dashboard

Menu:

```text
Dashboard > Abrir Dashboard
```

Use o dashboard para acompanhar:

- volume de QSOs
- bandas e modos ativos
- horarios de operacao
- top callsigns
- indicadores estimados de DXCC, CQ e WPX

## Integracao com JTDX ou WSJT-X

Menu:

```text
Configuracoes > Integracoes > JTDX / Club Log
```

Para iniciar:

1. habilite o listener `UDP`
2. defina `host` e `porta`
3. configure o `JTDX` ou `WSJT-X` para enviar `Logged ADIF`
4. acompanhe o resultado em `Configuracoes > Integracoes > Monitor`

## Onde procurar ajuda

- guia completo: [guia_do_usuario_pt-BR.md](guia_do_usuario_pt-BR.md)
- FAQ: [faq_pt-BR.md](faq_pt-BR.md)
- integracoes: [integracoes.md](integracoes.md)
- importacao ADIF: [importacao_adif.md](importacao_adif.md)
