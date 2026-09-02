# vendor/ — ferramentas de terceiros

Estas ferramentas são **opcionais**: sem elas a aplicação funciona, apenas
compacta mais devagar (usa o `zipfile` do Python) e não envia à nuvem.

```
python vendoraixar_ferramentas.py   baixa da origem oficial
python vendor\conferir.py             mostra o que foi encontrado e de onde
```

O `build_exe.bat` embute automaticamente o que estiver aqui.

## A arrumação da pasta é livre

A busca aceita qualquer estrutura e escolhe a arquitetura desta máquina:

```
vendor/7zip/7za.exe              pasta arrumada
vendor/7za/x64/7za.exe           pacote "7-Zip Extra" extraído inteiro
vendor/qualquer/nome/7za.exe     também funciona
vendor/rclone/rclone.exe
```

A aplicação procura aqui **antes** do sistema, então dá para atualizar uma
ferramenta trocando o arquivo, sem recompilar.

## Tamanho

O rclone passa de 80 MB. Se o executável ficar grande demais para distribuir,
deixe esta pasta **ao lado do `.exe`** em vez de dentro dele — funciona igual e
o executável fica pequeno.

## Licenças

Quem distribui o instalador é responsável por cumpri-las. O `conferir.py` avisa
quando um binário vai sem o texto da licença.

| Ferramenta | Licença | Obrigação principal |
|---|---|---|
| 7-Zip (`7za.exe`, pacote *7-Zip Extra*) | LGPL 2.1+ | Distribuir o texto da licença junto |
| rclone | MIT | Manter o aviso de copyright |

Confira o SHA-256 que o script de download imprime contra o publicado no site
oficial antes de distribuir.
