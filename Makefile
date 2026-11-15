PYTHON ?= python3
LATEXMK ?= latexmk
BUILD := output/.build
PDF := output/linux-c-book.pdf

.PHONY: all pdf convert fetch images verify clean check-snapshot
all: pdf

pdf:
	mkdir -p $(BUILD)
	$(LATEXMK) -xelatex -interaction=nonstopmode -halt-on-error -file-line-error \
		-latexoption=-no-shell-escape \
		-outdir=$(BUILD) -jobname=linux-c-book main.tex
	cp $(BUILD)/linux-c-book.pdf $(PDF)

convert: check-snapshot
	$(PYTHON) scripts/convert.py

fetch:
	$(PYTHON) scripts/fetch.py

images:
	$(PYTHON) scripts/prepare_images.py

verify: check-snapshot
	$(PYTHON) scripts/verify.py

check-snapshot:
	@test -f source-html/index.html || { \
		printf '%s\n' '需要原站快照。请按 README 中的「恢复原站快照」说明操作。' >&2; \
		exit 1; \
	}

clean:
	rm -rf $(BUILD)
