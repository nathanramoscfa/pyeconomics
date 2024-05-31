import os
import re
from setuptools import setup, find_packages


# Function to extract the version from __version__.py
def get_version():
    here = os.path.abspath(os.path.dirname(__file__))
    with (open(
        os.path.join(here, '__version__.py'),
        encoding='utf-8'
    ) as version_file):
        version_file_contents = version_file.read()
    # Use regular expression to extract version string
    version_match = re.search(
        r"^__version__ = ['\"]([^'\"]*)['\"]",
        version_file_contents,
        re.M
    )
    if version_match:
        return version_match.group(1)
    raise RuntimeError("Unable to find version string.")


# Read the contents of your requirements file
with open('requirements.txt', encoding='utf-8') as req_file:
    required = req_file.read().splitlines()

# Open and read the README file for the long description
with open('README.md', encoding='utf-8') as readme_file:
    long_description = readme_file.read()

setup(
    name='pyeconomics',
    version=get_version(),
    author='Nathan Ramos, CFA',
    author_email='nathan.ramos.github@gmail.com',
    packages=find_packages(),
    include_package_data=True,
    description='A library for economic and financial analysis',
    long_description=long_description,
    long_description_content_type='text/markdown',
    url='https://github.com/nathanramoscfa/pyeconomics',
    install_requires=required,
    classifiers=[
        'Development Status :: 3 - Alpha',
        'Intended Audience :: Developers',
        'Intended Audience :: Financial and Insurance Industry',
        'Programming Language :: Python :: 3.10',
        'Programming Language :: Python :: 3.11',
        'Programming Language :: Python :: 3.12',
        'License :: OSI Approved :: MIT License',
        'Operating System :: OS Independent',
        'Topic :: Office/Business :: Financial',
        'Topic :: Office/Business :: Financial :: Investment'
    ],
    python_requires='>=3.10, <3.13',
    project_urls={
        'Bug Reports': 'https://github.com/nathanramoscfa/pyeconomics/issues',
        'Source': 'https://github.com/nathanramoscfa/pyeconomics',
    },
)
