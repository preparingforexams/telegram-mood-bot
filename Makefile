.PHONY: all

all: code.zip layer.zip

code.zip: $(wildcard *.py)
	zip code.zip *.py

python: requirements.txt
	pip install -r requirements.txt -t python

layer.zip: python
	zip -r layer.zip python
