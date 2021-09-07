import os
from setuptools import setup, find_packages


with open(os.path.join(os.path.dirname(__file__), 'README.md')) as readme:
    README = readme.read()

with open(os.path.join(os.path.dirname(__file__), 'requirements.txt')) as requirements:
    REQUIREMENTS = requirements.read()


setup(
    name="djangosaml2-spid",
    version='1.1.4',
    description="Djangosaml2 SPID Service Provider",
    long_description=README,
    long_description_content_type='text/markdown',
    author='Giuseppe De Marco',
    author_email='demarcog83@gmail.com',
    license="Apache 2.0",
    url='https://github.com/italia/djangosaml2_spid',
    packages=find_packages('src'),
    package_dir={'': 'src'},
    include_package_data=True,
    classifiers=[
        "Development Status :: 5 - Production/Stable",
        "License :: OSI Approved :: Apache Software License",
        "Programming Language :: Python :: 3.6",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        'Programming Language :: Python :: Implementation :: CPython',
        "Topic :: Software Development :: Libraries :: Python Modules"],
    install_requires=REQUIREMENTS,
    zip_safe=False,
)
