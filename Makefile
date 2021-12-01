.PHONY: all, apply

all: code.zip layer.zip

code.zip: $(wildcard *.py)
	rm code.zip || TRUE
	zip code.zip *.py

python: requirements.txt
	rm -rf python || TRUE
	pip install -r requirements.txt -t python

layer.zip: python
	rm layer.zip || TRUE
	zip -r layer.zip python

apply: code.zip layer.zip
	cd terraform && terraform apply
