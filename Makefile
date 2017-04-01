.PHONY: test test-html
test:
	coverage run --branch -m unittest discover
	coverage report -m

test-html: test
	coverage html

