from setuptools import setup, find_packages

setup(
    name="zotero_topic_modeling",
    version="0.1",
    packages=find_packages(),
    install_requires=[
        'pyzotero',
        'pdfminer.six',
        'gensim',
        'nltk',
        'matplotlib',
        'numpy',
        'requests',
        'sentence-transformers',
        'faiss-cpu',
    ],
)
