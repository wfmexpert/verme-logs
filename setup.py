import os
from setuptools import find_packages, setup

with open(os.path.join(os.path.dirname(__file__), 'README.rst')) as readme:
    README = readme.read()

# allow setup.py to be run from any path
os.chdir(os.path.normpath(os.path.join(os.path.abspath(__file__), os.pardir)))

setup(
    name='verme-logs',
    version='1.22',
    packages=find_packages(),
    include_package_data=True,
    license='BSD License',  # example license
    description='Verme logs module to catch server processes and client browser errors',
    long_description=README,
    url='https://www.verme.ru/',
    author='Ilya Tabakov',
    author_email='i.tabakov@verme.ru',
    install_requires=[
        'social-auth-app-django',
        'social-auth-core[saml]',
        'xlrd',
        'XlsxWriter',
        'xlwt',
        'django-axes',
    ],
    classifiers=[
        'Environment :: Web Environment',
        'Framework :: Django',
        'Framework :: Django :: 2.0',  # replace "X.Y" as appropriate
        'Intended Audience :: Developers',
        'License :: OSI Approved :: BSD License',  # example license
        'Operating System :: OS Independent',
        'Programming Language :: Python',
        'Programming Language :: Python :: 3.5',
        'Programming Language :: Python :: 3.6',
        'Topic :: Internet :: WWW/HTTP',
        'Topic :: Internet :: WWW/HTTP :: Dynamic Content',
    ],
)
