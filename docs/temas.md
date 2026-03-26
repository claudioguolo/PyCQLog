# Temas

## Objetivo

O `PyCQLog` agora possui suporte inicial a temas para evitar problemas de contraste em ambientes claros e escuros.

## Modos disponiveis

- `system`
- `light`
- `dark`

## Arquivos principais

- [src/pycqlog/themes.py](../src/pycqlog/themes.py)
- [src/pycqlog/interfaces/desktop/main_window.py](../src/pycqlog/interfaces/desktop/main_window.py)
- [src/pycqlog/interfaces/desktop/settings_dialog.py](../src/pycqlog/interfaces/desktop/settings_dialog.py)

## Como funciona

- `system` tenta seguir a aparencia do tema do sistema operacional
- `light` aplica uma paleta clara fixa
- `dark` aplica uma paleta escura fixa

## Evolucoes futuras

- temas customizados por arquivo
- ajuste fino de fontes e densidade visual
- sincronizacao dinamica com mudancas do sistema operacional
