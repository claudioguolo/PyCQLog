# Fluxo de Registro de QSO

## Objetivo

O primeiro fluxo formal do sistema Python e o registro manual de QSO.

## Etapas

### 1. Captura

A janela principal coleta:

- callsign
- data
- hora
- frequencia
- modo
- RST enviado
- RST recebido
- operador
- estacao
- notas

### 2. Comando

A interface transforma os campos em um `SaveQsoCommand`.

Arquivo relacionado:

- [src/pycqlog/application/dto.py](../src/pycqlog/application/dto.py)

### 3. Normalizacao

O caso de uso padroniza:

- callsign em caixa alta
- modo em caixa alta
- operador e estacao em caixa alta
- valores textuais sem espacos excedentes

### 4. Enriquecimento

O sistema infere a banda com base na frequencia informada.

Exemplo:

- `14.074` -> `20m`

### 5. Validacao

O fluxo bloqueia salvamento quando:

- o callsign esta vazio
- a frequencia e menor ou igual a zero
- o modo esta vazio

O fluxo gera aviso quando:

- a frequencia nao cai em uma faixa mapeada

### 6. Persistencia

Na versao atual, o QSO e salvo em SQLite dentro do logbook ativo.

### 7. Resposta para UI

A interface recebe:

- identificador do QSO
- callsign normalizado
- banda
- modo
- avisos

### 8. Historico por callsign

Ao digitar ou selecionar um callsign, a interface consulta QSOs anteriores com correspondencia exata e exibe:

- data
- hora
- banda
- modo
- RST enviado e recebido

Isso ajuda o operador a recuperar contexto rapidamente antes de salvar um novo contato.

## Proximo nivel deste fluxo

As proximas evolucoes previstas para este caso de uso sao:

- listagem de QSOs salvos
- busca por callsign
- resolucao DXCC
- importacao ADIF
