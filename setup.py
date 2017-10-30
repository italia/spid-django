from setuptools import setup, find_packages

setup(
    name='django-spid',
    packages=find_packages(exclude='example'),
    include_package_data=True,
    zip_safe=False,
    version='0.0.1',
    description='Spid authentication app for django',
    author='',
    author_email='',
    url='https://github.com/spid-django-hack17/spid-django',
    keywords=['django', 'authentication', 'spid', 'italia'],
    classifiers=[
        'Intended Audience :: Developers',
        'Topic :: Software Development :: Libraries :: Python Modules',
        'Environment :: Web Environment',
        'Topic :: Internet',
        'Programming Language :: Python',
        'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: 3.3',
        'Programming Language :: Python :: 3.4',
        'Programming Language :: Python :: 3.5',
        'Framework :: Django',
    ],
)