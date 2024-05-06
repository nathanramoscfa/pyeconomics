from setuptools import setup, find_packages

setup(
    name='pyeconomics',
    version='0.1.0',
    author='Nathan Ramos, CFA',
    author_email='nathan.ramos.github@gmail.com',
    packages=find_packages(),
    description='A library for economic and financial analysis',
    long_description=open('README.md').read(),
    long_description_content_type='text/markdown',
    url='https://github.com/nathanramoscfa/pyeconomics',
    install_requires=[
        # Dependencies, e.g., 'numpy', 'pandas'
    ],
    classifiers=[
        'Development Status :: 3 - Alpha',
        'Intended Audience :: Developers',
        'Programming Language :: Python :: 3',
        'License :: OSI Approved :: MIT License'
    ]
)
