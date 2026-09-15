PY ?= python
VENV ?= .venv
BIN := $(VENV)/bin
ifeq ($(OS),Windows_NT)
BIN := $(VENV)/Scripts
endif

.PHONY: setup test data notebooks clean

setup:
	$(PY) -m venv $(VENV)
	$(BIN)/python -m pip install --upgrade pip
	$(BIN)/python -m pip install -r requirements.txt
	$(BIN)/python -m ipykernel install --user --name arena-lab --display-name "arena-lab"

test:
	$(BIN)/python -m pytest -q tests

data:
	$(BIN)/python scripts/download_data.py

notebooks:
	$(BIN)/python -m jupyter nbconvert --to notebook --execute --inplace --ExecutePreprocessor.kernel_name=arena-lab --ExecutePreprocessor.timeout=3600 notebooks/01_donde_buscar_arena.ipynb
	$(BIN)/python -m jupyter nbconvert --to notebook --execute --inplace --ExecutePreprocessor.kernel_name=arena-lab --ExecutePreprocessor.timeout=3600 notebooks/02_la_logistica_de_la_arena.ipynb
	$(BIN)/python -m jupyter nbconvert --to notebook --execute --inplace --ExecutePreprocessor.kernel_name=arena-lab --ExecutePreprocessor.timeout=3600 notebooks/03_la_ruta_paga_el_pozo.ipynb

clean:
	rm -rf data/processed/*.parquet
