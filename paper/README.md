# Paper

The MSc thesis *Plain Language Summarization of Clinical Trials* (Grigorios Barmpas,
Aristotle University of Thessaloniki, supervised by Dr. Grigorios Tsoumakas), rewritten on
the full rebuilt dataset.

- [`main.pdf`](main.pdf): the typeset thesis.
- `main.tex`, `Chapters/`, `Appendices/`, `Tables/`, `Figures/`, `bibliography.bib`,
  `MastersDoctoralThesis.cls`: the LaTeX source.
- `web/build_web.py`: converts the source into the article on the web app's **Paper** page.

## Build the PDF

```bash
cd paper
latexmk -pdf main.tex     # pdflatex + biber
```

The table bodies in `Tables/*_body.tex` are generated from the experiment CSVs:
`python3 Tables/make_tables.py <path-to-paper_results/tables>`.

## Update the web version

After editing the LaTeX, regenerate the article from the repository root:

```bash
python paper/web/build_web.py --png-dir paper_results/figures
```

This writes `frontend/src/content/paper.json` and `frontend/public/paper/figures/`. The
thesis figures are PDFs, so `--png-dir` must hold a PNG with the same name for each one (the
plotting scripts write both). The converter handles exactly the LaTeX this thesis uses and
stops with an error on anything else, so a new macro has to be taught to it rather than
being silently dropped. Section, figure and table numbers follow LaTeX's own numbering.

The full-study numbers on the Landing and Model comparison pages come from the same result
tables:

```bash
python paper/web/build_results.py --tables paper_results/tables
```

It writes `frontend/src/content/thesis_results.json` and checks the corpus counts against the
text of Chapter 3.

