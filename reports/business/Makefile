LATEX_LIB := $(HOME)/vmiozzo-latex-library
REPORT := country_screening_business

TEXINPUTS := .:$(LATEX_LIB)/styles/:$(LATEX_LIB)/assets/:$(LATEX_LIB)/snippets/:

.PHONY: pdf force clean

pdf:
	TEXINPUTS="$(TEXINPUTS)" latexmk -pdf -interaction=nonstopmode -file-line-error $(REPORT).tex

force:
	TEXINPUTS="$(TEXINPUTS)" latexmk -g -pdf -interaction=nonstopmode -file-line-error $(REPORT).tex

clean:
	latexmk -C $(REPORT).tex
	rm -f *.aux *.bbl *.bcf *.blg *.fdb_latexmk *.fls *.log *.out *.run.xml *.synctex.gz *.toc
