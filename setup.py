from setuptools import setup

setup(
    # Needed to silence warnings (and to be a worthwhile package)
    name='hanneshelpers',
    url='https://github.com/hannesrosenbusch/hanneshelpers',
    author='Hannes Rosenbusch',
    author_email='',
    # Needed to actually package something
    packages=['hanneshelpers'],
    # Needed for dependencies
    install_requires=['easynmt==2.0.1'],
    # *strongly* suggested for sharing
    version='0.1',
    # The license can be anything you like
    license='MIT',
    description='bunch of my functions',
    # We will also need a readme eventually (there will be a warning)
    # long_description=open('README.txt').read(),
)