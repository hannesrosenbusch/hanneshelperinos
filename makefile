install:
	pip install -r requirements.txt

lint:
	pylint hanneshelpers/surveyexport.py
	pylint test_surveyexport.py

test:
	python3 -m pytest -vv -cov=go test_surveyexport.py