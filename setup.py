from setuptools import setup, find_packages

setup(
    name='hanneshelpers',
    url='https://github.com/hannesrosenbusch/hanneshelpers',
    author='Hannes Rosenbusch',
    author_email='',
    package_dir = {
    'surveyexport': 'surveyexport',
    'sentiment': 'sentiment'},
    packages=find_packages(),
    install_requires=['easynmt==2.0.1', 'python-docx'],
    version='0.1',
    license='MIT',
    description='bunch of my functions',
)