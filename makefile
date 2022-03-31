install:
	pip install -r requirements.txt

#lint:
#	pylint --generated-members="torch.*" maximize.py

test:
	python3 -m pytest -vv -cov=go test_surveyexport.py