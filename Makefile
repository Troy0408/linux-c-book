PYTHON ?= python3
LATEXMK ?= latexmk
BUILD := output/.build
PDF := output/linux-c-book.pdf

.PHONY: all pdf convert fetch images verify clean
all: pdf

pdf:
	mkdir -p $(BUILD)
	$(LATEXMK) -xelatex -interaction=nonstopmode -halt-on-error -file-line-error \
		-latexoption=-no-shell-escape \
		-outdir=$(BUILD) -jobname=linux-c-book main.tex
	cp $(BUILD)/linux-c-book.pdf $(PDF)

convert:
	$(PYTHON) scripts/convert.py

fetch:
	$(PYTHON) scripts/fetch.py

images:
	$(PYTHON) scripts/prepare_images.py

verify:
	$(PYTHON) scripts/verify.py

clean:
	rm -rf $(BUILD)
