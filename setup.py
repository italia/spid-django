"""The setup module for django_spid.
See:
https://github.com/fangli/django_spid
"""

from codecs import open
from setuptools import (setup, find_packages)
from os import path

here = path.abspath(path.dirname(__file__))

# Get the long description from the README file
with open(path.join(here, 'README.md'), encoding='utf-8') as f:
    long_description = f.read()

setup(
    name='django_spid',

    version='0.1',

    description='Django SPID Authentication Made Easy. Easily integrate with SPID Italian Identity Providers',
    long_description=long_description,

    url='https://github.com/pdpfsug/spid-django',

    author='PDP Free Software User Group <info@pdp.linux.it>',
    author_email='info@pdp.linux.it',

    license='Apache 2.0',

    classifiers=[
        #   3 - Alpha
        #   4 - Beta
        #   5 - Production/Stable
        'Development Status :: 3 - Alpha',

        'Intended Audience :: Developers',
        'Topic :: Software Development :: Libraries :: Python Modules',

        'License :: OSI Approved :: Apache Software License',

        'Framework :: Django :: 1.5',
        'Framework :: Django :: 1.6',
        'Framework :: Django :: 1.7',
        'Framework :: Django :: 1.8',
        'Framework :: Django :: 1.9',
        'Framework :: Django :: 1.10',

        'Programming Language :: Python :: 2',
        'Programming Language :: Python :: 2.6',
        'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.3',
        'Programming Language :: Python :: 3.4',
        'Programming Language :: Python :: 3.5',
        'Programming Language :: Python :: 3.6',
    ],

    keywords='Django SPID Authentication Made Easy, integrate with SPID easily',

    packages=find_packages(),

    install_requires=[],
    include_package_data=True,
)
