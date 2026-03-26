# Interface Desktop PyQt

## Objetivo

O desktop PyQt sera a interface principal da primeira versao operacional do `PyCQLog`.

## Composicao atual

A interface atual possui:

- janela principal
- menu da aplicacao
- dialogos de configuracao por area
- suporte a tema do sistema, claro e escuro
- formulario de entrada manual de QSO
- busca por callsign
- tabela de QSOs recentes
- painel de historico por callsign
- selecao de logbook ativo
- edicao de QSO pela selecao da tabela
- exclusao de QSO com confirmacao
- selecao de idioma
- dialogo About
- mensagens de validacao
- mensagem visual de sucesso
- monitor de integracoes

Arquivos atuais:

- [src/pycqlog/interfaces/desktop/app.py](../src/pycqlog/interfaces/desktop/app.py)
- [src/pycqlog/interfaces/desktop/main_window.py](../src/pycqlog/interfaces/desktop/main_window.py)

## Regras de implementacao

Para manter a base saudavel:

- a janela deve delegar gravacao para casos de uso
- a janela nao deve resolver banda, DXCC ou validacao de negocio diretamente
- mensagens de erro devem refletir falhas do dominio/aplicacao
- widgets novos devem ser organizados para facilitar extracao em componentes

## Evolucao recomendada da UI

Ordem sugerida:

1. separar formulario em widget proprio
2. adicionar menu principal e acoes basicas
3. ampliar filtros de busca
4. preparar janelas auxiliares para configuracao e integracoes
5. adicionar atalhos de teclado para operacao rapida

## Direcao visual

A interface deve priorizar:

- foco em operacao rapida
- poucos cliques para registrar contato
- campos claros para uso em radio-operacao
- feedback imediato apos salvar
