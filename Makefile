.PHONY: test test-html tests-install
test:
	coverage run --branch -m unittest discover
	coverage report -m

test-html: test
	coverage html

test-install:
	pip install --user -r test-requirements.txt

