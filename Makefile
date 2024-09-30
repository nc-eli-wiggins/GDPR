#################################################################################
#
# Makefile to build the project
#
#################################################################################

PROJECT_NAME = de-northcoders-GDPR
REGION = eu-west-2
PYTHON_INTERPRETER = python
WD=$(shell pwd)
PYTHONPATH=${WD}
SHELL := /bin/bash
PROFILE = default
PIP:=pip
ROOT_DIR := $(shell pwd)

## Create python interpreter environment.
create-environment:
	@echo ">>> About to create environment: $(PROJECT_NAME)..."
	@echo ">>> check python3 version"
	( \
		$(PYTHON_INTERPRETER) --version; \
	)
	@echo ">>> Setting up VirtualEnv."
	( \
		export PYTHONPATH=$(ROOT_DIR);\
	    $(PIP) install -q virtualenv virtualenvwrapper; \
	    virtualenv myenv --python=$(PYTHON_INTERPRETER); \
	)

# Define utility variable to help calling Python from the virtual environment
ACTIVATE_ENV := source myenv/bin/activate

# Execute python related functionalities from within the project's environment
define execute_in_env
	$(ACTIVATE_ENV) && $1
endef

## Build the environment requirements
requirements: create-environment
	$(call execute_in_env, $(PIP) install -r ./requirements.txt)

################################################################################################################
# Set Up
## Install bandit
bandit:
	$(call execute_in_env, $(PIP) install bandit)

## Install safety
safety:
	$(call execute_in_env, $(PIP) install safety)


## Install coverage
coverage:
	$(call execute_in_env, $(PIP) install coverage)

## Run the security test (bandit + safety)
security-test:
	$(call execute_in_env, safety check -r ./requirements.txt)
	$(call execute_in_env, bandit -lll */*.py *c/*/*.py)


## Run the all unit tests
unit-test:
	$(call execute_in_env, PYTHONPATH=${PYTHONPATH} pytest -v)

check-coverage:
	$(call execute_in_env, PYTHONPATH=${PYTHONPATH} coverage run --omit 'myenv/*' -m pytest -vvv && coverage report -m)

############################################################################################################

## create dummy data file
data:
	$(call execute_in_env, PYTHONPATH=${PYTHONPATH} python src/data/create_data.py)

## upload dummy data file to s3 input bucket
upload:
	$(call execute_in_env, PYTHONPATH=${PYTHONPATH} python src/utils/upload.py)

## invoke the function
invoke:
	$(call execute_in_env, PYTHONPATH=${PYTHONPATH} python src/utils/create_json_payload.py)

