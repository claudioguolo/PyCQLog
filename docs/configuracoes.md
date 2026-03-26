# Configuracoes

## Objetivo

O `PyCQLog` agora possui configuracoes organizadas por submenu no menu principal.

## Arquivos principais

- [src/pycqlog/infrastructure/settings.py](../src/pycqlog/infrastructure/settings.py)
- [src/pycqlog/interfaces/desktop/directories_dialog.py](../src/pycqlog/interfaces/desktop/directories_dialog.py)
- [src/pycqlog/interfaces/desktop/adif_settings_dialog.py](../src/pycqlog/interfaces/desktop/adif_settings_dialog.py)
- [src/pycqlog/interfaces/desktop/main_window.py](../src/pycqlog/interfaces/desktop/main_window.py)

## Configuracoes atuais

- idioma da interface
- tema da interface
- logbook ativo
- cores do dashboard
- callsign padrao do operador
- callsign padrao da estacao
- diretorio de dados
- diretorio padrao dos logs
- prefixo padrao do arquivo de exportacao ADIF

## Comportamento atual

- as configuracoes sao salvas em um `settings.json` estavel no diretorio de configuracao
- o idioma e aplicado imediatamente na interface
- o tema pode ser alterado diretamente pelo submenu `Tema`
- o logbook ativo pode ser alterado diretamente na janela principal
- o submenu `Logbooks` permite criar e associar perfis padrao por operacao
- o submenu `Perfis` permite manter cadastros reutilizaveis de operador e estacao
- o submenu `Dashboard` dentro de `Configuracoes` controla as cores por banda e por modo nos graficos
- o submenu `Dashboard` tambem pode aplicar essas cores nas tabelas principais e no historico
- operador e estacao padrao sao configurados pelo submenu `ADIF`
- operador e estacao padrao sao reutilizados no formulario principal
- o diretorio de dados configurado passa a ser usado pelo banco local na proxima inicializacao
- o submenu `Diretorios` possui dialogo proprio para os caminhos
- ao abrir, o dialogo `Diretorios` usa aproximadamente 50% da largura da janela principal
- o dialogo permite escolher visualmente o diretorio de dados
- o diretorio padrao dos logs e usado como pasta inicial para importacao ADIF
- o dialogo permite escolher visualmente o diretorio padrao dos logs
- as preferencias ADIF permitem definir operador, estacao e prefixo padrao da exportacao
- os caminhos sao validados antes de salvar

## Proximo passo natural

- incluir preferencias operacionais adicionais
- adicionar validacoes mais ricas e testes para configuracoes
