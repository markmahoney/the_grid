generate: setup
	source venv/bin/activate; python grid.py; deactivate

setup: venv/setup

venv/setup: requirements.txt
	test -d venv || python3 -m venv venv
	source venv/bin/activate; pip install -Ur requirements.txt; deactivate
	touch venv/bin/activate

clean:
	rm -r venv
