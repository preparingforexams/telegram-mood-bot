.PHONY: all, apply

all: code.zip layer.zip

code.zip: $(wildcard *.py)
	rm code.zip || true
	zip code.zip *.py

python: requirements.txt
	rm -rf python || true
	pip install -r requirements.txt -t python

layer.zip: python
	rm layer.zip || true
	zip -r layer.zip python

init:
	cd terraform && terraform init

apply: code.zip layer.zip
	cd terraform && terraform apply
