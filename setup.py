import io
import os
from setuptools import setup, find_packages

STATUS_PROD = 'Development Status :: 5 - Production/Stable'
STATUS_BETA = 'Development Status :: 4 - Beta'
STATUS_ALPHA = 'Development Status :: 3 - Alpha'

version = '0.2.2'
README = os.path.join(os.path.dirname(__file__), 'README.rst')
long_description = io.open(README, 'rt', encoding='utf-8').read()
setup(
    name='django-simple-audit-gizmag',
    version=version,
    description="Simple audit for model instances in Django.",
    long_description=long_description,
    classifiers=[
        STATUS_BETA,
        'Environment :: Web Environment',
        'Framework :: Django',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: BSD License',
        'Operating System :: OS Independent',
        'Topic :: Software Development :: Libraries :: Python Modules',
        'Topic :: Utilities',

        # Generally, we support the following.
        "Programming Language :: Python",
        "Programming Language :: Python :: 2",
        "Programming Language :: Python :: 3",
        "Framework :: Django",

        # Specifically, we support the following releases.
        "Programming Language :: Python :: 2.7",
        "Programming Language :: Python :: 3.4",
        "Programming Language :: Python :: 3.5",
        "Framework :: Django :: 1.8",
        "Framework :: Django :: 1.9",
    ],
    keywords='revisions versioning history audit',
    author='Gizmag',
    author_email='opensource@gizmag.com',
    url='https://github.com/gizmag/django-simple-audit',
    license='BSD',
    packages=find_packages('.', exclude=('testproject*',)),
    include_package_data=True,
    install_requires=[
        'Django>=1.8',
    ],
    zip_safe=False,
    test_suite='testproject.manage.run_tests',
)
