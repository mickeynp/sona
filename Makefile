init:
	pip install -r requirements.txt --use-mirrors
install:
	python setup.py install
test:
	nosetests -v --failed --with-coverage --cover-package=sona tests
