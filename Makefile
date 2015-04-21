REQUIREMENTS_FILE=requirements.txt
REQUIREMENTS_OUT=requirements.txt.log
SETUP_OUT=*.egg-info


all: setup requirements model_upgrade

requirements: setup $(REQUIREMENTS_OUT)

piprot:
	piprot -x $(REQUIREMENTS_FILE)

$(REQUIREMENTS_OUT): $(REQUIREMENTS_FILE)
	pip install -r $(REQUIREMENTS_FILE) | tee -a $(REQUIREMENTS_OUT)
	python setup.py develop

setup: virtualenv $(SETUP_OUT)

$(SETUP_OUT): setup.py setup.cfg
	python setup.py develop
	touch $(SETUP_OUT)

clean:
	find . -name "*.py[oc]" -delete
	find . -name "__pycache__" -delete
	rm $(REQUIREMENTS_OUT)

test: requirements
	nosetests

virtualenv:
ifndef VIRTUAL_ENV
	$(error No VIRTUAL_ENV defined)
endif


## Develop:

INI_FILE=development.ini

develop: requirements
	screen -c develop.screenrc

serve: requirements
	pserve --reload $(INI_FILE)

shell: requirements
	pshell $(INI_FILE)

fixtures: requirements
	echo "model.drop_all(); model.create_all(); fixtures.populate_dev()" | pshell $(INI_FILE) -p python
	alembic -c $(INI_FILE) stamp head 2>&1 | tee -a $(ALEMBIC_OUT)


## Celery:

celery: requirements
	INI_FILE=$(INI_FILE) celery worker -B --app=briefmetrics.tasks.setup --loglevel INFO


## Database:

ALEMBIC_VERSIONS=migration/versions/
ALEMBIC_OUT=alembic.log

$(ALEMBIC_OUT): $(ALEMBIC_VERSIONS)
	alembic -c $(INI_FILE) upgrade head 2>&1 | tee -a $(ALEMBIC_OUT)

model_create:
	echo "model.create_all();" | pshell $(INI_FILE) -p python
	alembic -c $(INI_FILE) stamp head 2>&1 | tee -a $(ALEMBIC_OUT)

model_stamp:
	alembic -c $(INI_FILE) stamp head 2>&1 | tee -a $(ALEMBIC_OUT)

model_diff:
	alembic -c $(INI_FILE) revision --autogenerate --sql

model_save:
	# Note: This target is for development purposes only, as it requires user input.
	@echo "Enter alembic revision message: "
	@read message; alembic -c $(INI_FILE) revision --autogenerate -m "$$message"

model_upgrade: $(ALEMBIC_OUT)
