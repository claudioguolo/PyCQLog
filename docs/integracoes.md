# Integracoes

## Objetivo

O `PyCQLog` agora possui a base para integracao automatica com `WSJT-X / JTDX`, envio em tempo real para `Club Log` e `QRZ.com`, alem da busca inteligente por Callbook e assinatura oficial via `LoTW (TQSL)`.

## Componentes

- listener UDP compatível com mensagens `Logged ADIF` do protocolo WSJT-X/JTDX
- processamento do ADIF recebido para gravacao automatica no logbook ativo
- filas de envio paralelas para `Club Log` e `QRZ.com Logbook API` com intervalo minimo configuravel
- controle de autoenvio por origem, incluindo `WSJT-X / JTDX` e QSOs manuais
- callbook integrado com `QRZ.com XML API` para auto-completar indicativos
- gerador de arquivo criptografado via shell local para `LoTW (.tq8)` usando a aplicacao nativa `tqsl`
- dialogo de configuracao estruturado por Abas no menu `Configuracoes > Integracoes`
- monitor visual de eventos no menu `Configuracoes > Integracoes > Monitor`
- fila persistente de uploads pendentes (`Club Log` e `QRZ`) caso ocorram falhas de rede.

## Fluxo atual

1. o `WSJT-X / JTDX` envia o evento `Logged ADIF` por UDP
2. o `PyCQLog` recebe o datagrama configurado na porta local
3. o ADIF e interpretado e salvo como novo QSO no logbook ativo
4. se o `Club Log` estiver habilitado e a origem estiver autorizada, o mesmo ADIF entra na fila de upload
5. o uploader respeita um intervalo minimo entre envios
6. o monitor de integracao exibe os eventos recebidos e o resultado dos uploads
7. uploads pendentes do `Club Log` ficam salvos no diretorio de configuracao para nova tentativa futura

## Observacoes importantes

- a primeira versao trabalha com o evento `Logged ADIF`, que e a forma mais robusta para aproveitar o ADIF completo emitido pelo software externo
- o endpoint padrao do `Club Log` ficou configurado como `https://clublog.org/realtime.php`
- o envio ao `Club Log` exige email, app password, callsign principal e API key configurados
- o monitor agora mostra melhor o estado real do listener UDP e da prontidao do `Club Log`
- o contador de awards no dashboard continua local e independente do `Club Log`

## Limitacoes atuais

- ainda nao ha reconciliacao de QSO confirmado com servicos externos
- ainda nao ha detalhamento por job alem do historico simples do monitor
- ainda nao foi adicionada leitura de outros protocolos como `fldigi`
