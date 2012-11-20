"""
Flask-Alchemy
---------------

Various SQLAlchemy helpers for Flask, built on top of Flask-SQLAlchemy.
"""

from setuptools import setup, Command
import subprocess


class PyTest(Command):
    user_options = []

    def initialize_options(self):
        pass

    def finalize_options(self):
        pass

    def run(self):
        errno = subprocess.call(['py.test'])
        raise SystemExit(errno)

setup(
    name='flask-alchemy',
    version='0.1.1',
    url='https://github.com/kvesteri/flask-alchemy',
    license='BSD',
    author='Konsta Vesterinen',
    author_email='konsta@fastmonkeys.com',
    description=(
        'Various SQLAlchemy helpers for Flask, '
        'built on top of Flask-SQLAlchemy.'
    ),
    long_description=__doc__,
    packages=['flask_alchemy'],
    zip_safe=False,
    include_package_data=True,
    platforms='any',
    install_requires=[
        'SQLAlchemy>=0.7',
        'Flask>=0.8',
        'WTForms>=1.0.1'
    ],
    cmdclass={'test': PyTest},
    classifiers=[
        'Environment :: Web Environment',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: BSD License',
        'Operating System :: OS Independent',
        'Programming Language :: Python',
        'Topic :: Internet :: WWW/HTTP :: Dynamic Content',
        'Topic :: Software Development :: Libraries :: Python Modules'
    ]
)
