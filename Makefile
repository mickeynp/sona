init:
	pip install -r requirements.txt --use-mirrors

test:
	nosetests -v --rednose --failed --with-coverage --cover-package=pysemantic tests
