# FAQ - pt-BR

## O `PyCQLog` ja pode ser usado no dia a dia?

Sim. A aplicacao ja suporta operacao local com registro manual, importacao e exportacao ADIF, multiplos logbooks, dashboard e integracao inicial com `WSJT-X / JTDX`.

## Onde meus dados ficam gravados?

Os QSOs ficam em um banco `SQLite` local. O local do banco depende do `Diretorio de dados` configurado em `Configuracoes > Diretorios`.

## Posso usar mais de um log?

Sim. O sistema suporta multiplos `logbooks`, com selecao de log ativo.

## Posso trocar o idioma da interface?

Sim. Atualmente existem `pt-BR` e `en`, com estrutura preparada para novas traducoes.

## Posso usar tema escuro?

Sim. O sistema suporta `system`, `light` e `dark`.

## O sistema importa arquivos ADIF grandes?

Sim. O fluxo de importacao ja trabalha com preview, selecao individual, edicao de campos e deduplicacao basica.

## O sistema exporta ADIF com filtros?

Sim. A exportacao pode ser feita por `callsign`, `periodo`, `banda` e `modo`.

## O `JTDX` ou `WSJT-X` ja podem enviar QSOs automaticamente?

Sim, na integracao inicial via `UDP Logged ADIF`. O ideal e validar primeiro com o monitor de integracoes aberto.

## O envio para `Club Log` ja esta pronto?

Existe suporte inicial com fila persistente e monitoramento. Em ambiente real, a recomendacao e validar cuidadosamente credenciais, endpoint e comportamento da fila.

## O dashboard de awards e preciso?

Ele esta mais confiavel do que nas primeiras fases, porque agora usa uma base local curada de prefixos e matching mais conservador. Ainda assim, nao e uma base oficial completa de awards e nao deve ser tratado como fonte definitiva para confirmacoes.

## O sistema ja tem pacote `.deb`?

Ainda nao nesta base atual. A aplicacao esta preparada para isso como proximo passo de distribuicao.

## O que fazer se a interface nao abrir por erro do Qt?

Em sistemas Linux com `xcb`, instale:

```bash
sudo apt-get install -y \
  libxcb-cursor0 \
  libxcb-icccm4 \
  libxcb-image0 \
  libxcb-keysyms1 \
  libxcb-render-util0
```

## Onde comeco se eu quiser testar rapido?

Use primeiro:

- [inicio_rapido_pt-BR.md](inicio_rapido_pt-BR.md)
- [guia_do_usuario_pt-BR.md](guia_do_usuario_pt-BR.md)
