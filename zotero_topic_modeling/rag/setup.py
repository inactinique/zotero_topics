from setuptools import setup, find_packages

setup(
    name="zotero_topic_modeling",
    version="0.1",
    packages=find_packages(),
    install_requires=[
        'pyzotero',
        'pdfminer.six',
        'gensim<4.3.2',  # Use older version to avoid scipy dependency issues
        'nltk',
        'matplotlib',
        'numpy<1.25.0',  # Avoid newer versions that may have compatibility issues
        'requests',
        'pandas',
        'scikit-learn',
    ],
)
