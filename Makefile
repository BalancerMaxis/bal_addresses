.PHONY: docs
init:
	pip install -e .[socks]
	pip install -r bal_addresses/requirements.txt
	pip install -r bal_addresses/requirements-dev.txt
ci:
	pytest
