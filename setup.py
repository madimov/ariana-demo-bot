from setuptools import setup

setup(
    name="ariana_demo_bot",
    version="0.0.1",
    install_requires=[
        "gunicorn",
        "python-telegram-bot",
        "validate_email",
        "psycopg2-binary",
        "scikit-learn",
        "scipy",
        "sklearn-crfsuite",
        "cython==0.27.1"
    ],
    dependency_links=[
    "http://github.com/madimov/rasa_nlu_heroku/tarball/master#egg=rasa_nlu",
    "http://github.com/madimov/spacy_heroku/tarball/master#egg=spacy"
    ]
)