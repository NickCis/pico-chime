RSHELL=rshell

.PHONY=install repl help

help: # Muestra esta ayuda
	@grep -E '^[a-zA-Z0-9 -]+:.*#'  Makefile | sort | while read -r l; do printf "\033[1;32m$$(echo $$l | cut -f 1 -d':')\033[00m:$$(echo $$l | cut -f 2- -d'#')\n"; done

venv: # Para herramientas locales de python
	python3 -m venv venv

format: venv # Ejecuta autoformateo
	source ./venv/bin/activate && \
		pip install autopep8 && \
		autopep8 -i -r src

install: # Instala los archivos en Raspberry Pi Pico
	$(RSHELL) cp -r src/* /pyboard/

repl: Inicia micropython
	$(RSHELL) repl
