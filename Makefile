.PHONY: check-pandoc check-pypandoc check-twine test test-html tests-install dist-check dist-install dist-build dist-info dist-upload

# Log function from github.com/Noah-Huppert/make-log
NO_COLOR=\033[0m

OK_TAG=OK   #
OK_COLOR=\033[32;01m

WARN_TAG=WARN #
WARN_COLOR=\033[33;01m

ERROR_TAG=ERROR
ERROR_COLOR=\033[31;01m

define log = # level, message
$(if $(findstring ok, $(1)), @printf "$(OK_COLOR)[$(OK_TAG)] $(2)$(NO_COLOR)\n")
$(if $(findstring warn, $(1)), @printf "$(WARN_COLOR)[$(WARN_TAG)] $(2)$(NO_COLOR)\n")
$(if $(findstring error, $(1)), @printf "$(ERROR_COLOR)[$(ERROR_TAG)] $(2)$(NO_COLOR)\n")
endef

# Checks
check-pandoc:
ifeq (, $(shell which pandoc))
	$(call log,error,Pandoc not installed. Please install from pandoc.org)
	exit 1
endif

check-pypandoc: check-pandoc
ifeq ($(shell python -c "import pypandoc" 2> /dev/null; echo $$?),1)
	$(call log,error,pypandoc Python package not installed. Run dist-install target)
	exit 1
endif

check-twine:
ifeq (, $(shell which twine))
	$(call log,error,twine Python package not installed. Run dist-install target)
	exit 1
endif

# Testing
# Test with code coverage
test:
	$(call log,ok,Running tests)
	coverage run --branch --source py_i2c_register -m unittest discover
	coverage report -m

# Install packages required to test
test-install:
	$(call log,ok,Installing test requirements (test-requirments.txt))
	pip install --user -r test-requirements.txt

# Generate more detailed html coverage report
test-html: test
	$(call log,ok,Generating detailed coverage report)
	coverage html
	$(call log,ok,Detailed coverage report avaliable at htmlcov/index.html)

# Distribution
# Check packages required to distribute are installed
dist-check: check-pypandoc check-twine

# Install packages required to distribute
dist-install:
	$(call log,ok,Installing distribution requirments (dist-requirments.txt))
	pip install --user -r dist-requirements.txt

# Clean up distrubtion files
dist-clean:
	$(call log,ok,Cleaning distribution files)
	rm -rf dist *.egg-info

# Build package distribution
dist-build: dist-check
	$(call log,ok,Building distribution)
	python setup.py sdist

# Build package information
dist-info: dist-check
	$(call log,ok,Building package information)
	python setup.py egg_info

# Upload package to PyPi
dist-upload: dist-check
	$(call log,ok,Uploading package)
	twine upload dist/*
