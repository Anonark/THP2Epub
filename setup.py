import setuptools

with open("README.md", "r") as fh:
    long_description = fh.read()

setuptools.setup(
    name="thp2epub",
    version="1.1.2",
    author="Anonark",
    description="A touhou-project.com downloader",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/Anonark/THP2EPUB",
    packages=setuptools.find_packages(),
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
	install_requires=[
        'lxml>=0.0',
        'pyinstaller>=0.0'
        
    ]''',
    dependency_links=[
        'git+https://github.com/ceddlyburge/python_world#egg=python_world-0.0.1',
    ]'''
)
