from setuptools import setup, find_packages
from os import path

here = path.abspath(path.dirname(__file__))

setup(
    name='monitor',

    version='0.1.0',

    description='Monitor component of BIGSEA Asperathos framework',

    url='',

    author='Igor Natanael, Roberto Nascimento Jr.',
    author_email='',

    license='Apache 2.0',

    classifiers=[
        'Development Status :: 3 - Alpha',

        'Intended Audience :: Developers',
        'Topic :: Software Development :: Build Tools',

        'License :: OSI Approved :: Apache 2.0',

        'Programming Language :: Python :: 2.7',

    ],
    keywords='webservice monitoring monasca asperathos bigsea',

    packages=find_packages(exclude=['contrib', 'docs', 'tests*']),

    install_requires=['flask'],

    entry_points={
        'console_scripts': [
            'monitor=monitor.cli.main:main',
        ],
    },
)
