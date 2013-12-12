import setuptools
from os.path import join, dirname

setuptools.setup(
    name="django-passaporte-web",
    version="1.0.0",
    packages=["identity_client"],
    include_package_data=True,  # declarations in MANIFEST.in
    install_requires=open(join(dirname(__file__), 'requirements.txt')).readlines(),
    tests_require=[
        'django<=1.3.5',
    ],
    test_suite='runtests.runtests',
    author="vitormazzi",
    author_email="vitormazzi@gmail.com",
    url="http://github.com/myfreecomm/django-passaporte-web",
    license="Apache 2.0",
    description="Django client app for Passaporte Web.",
    long_description=open(join(dirname(__file__), "README.rst")).read(),
    keywords="django python passaporteweb",
    classifiers=[
        'Framework :: Django',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: Apache Software License',
        'Operating System :: OS Independent',
        'Topic :: Software Development',
    ],
)
