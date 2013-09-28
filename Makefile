REQUIREMENTS_FILE=requirements.txt
REQUIREMENTS_OUT=requirements.txt.log
SETUP_OUT=*.egg-info


all: setup requirements model_upgrade

requirements: $(REQUIREMENTS_OUT)

$(REQUIREMENTS_OUT): $(REQUIREMENTS_FILE)
	pip install -r $(REQUIREMENTS_FILE) | tee -a $(REQUIREMENTS_OUT)

setup: virtualenv $(SETUP_OUT)

$(SETUP_OUT): setup.py setup.cfg
	python setup.py develop
	touch $(SETUP_OUT)

clean:
	find . -name "*.py[oc]" -delete
	find . -name "__pycache__" -delete
	rm $(REQUIREMENTS_OUT)

test: setup requirements
	nosetests

virtualenv:
ifndef VIRTUAL_ENV
	$(error No VIRTUAL_ENV defined)
endif


## Develop:

INI_FILE=development.ini

develop: setup requirements
	screen -c develop.screenrc

serve: setup requirements
	pserve --reload $(INI_FILE)

shell: setup requirements
	pshell $(INI_FILE)

fixtures: setup requirements
	echo "model.drop_all(); model.create_all(); fixtures.populate_dev()" | pshell $(INI_FILE) -p python


### Database:

ALEMBIC_VERSIONS=migration/versions/
ALEMBIC_OUT=alembic.log

$(ALEMBIC_OUT): $(ALEMBIC_VERSIONS)
	alembic -c $(INI_FILE) upgrade head 2>&1 | tee -a $(ALEMBIC_OUT)

model_stamp:
	alembic -c $(INI_FILE) stamp head 2>&1 | tee -a $(ALEMBIC_OUT)

model_diff:
	alembic -c $(INI_FILE) revision --autogenerate --sql

model_save:
	# Note: This target is for development purposes only, as it requires user input.
	@echo "Enter alembic revision message: "
	@read message; alembic -c $(INI_FILE) revision --autogenerate -m "$$message"

model_upgrade: $(ALEMBIC_OUT)


## CSS:

css_watch:
	compass watch briefmetrics/web/compass

css:
	compass compile briefmetrics/web/compass

css_production:
	compass compile briefmetrics/web/compass --output-style compressed --force
