from setuptools import setup, find_packages

setup(
    name="zotero_topic_modeling",
    version="0.1",
    packages=find_packages(),
    install_requires=[
        'pyzotero',
        'PyPDF2',
        'gensim',
        'nltk',
        'matplotlib',
        'numpy',
        'requests',
    ],
)
