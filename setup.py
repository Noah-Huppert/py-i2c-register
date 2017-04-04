from setuptools import setup, find_packages

from codecs import open
from os import path

here = path.abspath(path.dirname(__file__))

try:
    import pypandoc
    long_description = pypandoc.convert(path.join(here, "README.md"), 'rst')
except(IOError, ImportError) as e:
    raise Exception("Failed to convert README.md to rst format, error: {}".format(e))

setup(
    name="py-i2c-register",
    version="0.0.8",
    description="Python wrapper library around the common I2C controller register pattern.",
    long_description=long_description,
    url="https://github.com/Noah-Huppert/py-i2c-register",
    author="Noah Huppert",
    author_email="developer.noah@gmail.com",
    license="MIT",

    # List of: https://pypi.python.org/pypi?%3Aaction=list_classifiers
    classifiers=[
        # Project maturity
        #   3 - Alpha
        #   4 - Beta
        #   5 - Production/Stable
        "Development Status :: 3 - Alpha",

        # Intended audience
        "Intended Audience :: Developers",
        "Topic :: Software Development :: Libraries :: Python Modules",

        "Programming Language :: Python :: 2",
        "Programming Language :: Python :: 3",
    ],

    keywords="library i2c registers",

    packages=find_packages(exclude=["contrib", "docs", "tests"]),

    install_requires=[],
    package_data={},
    data_files=[
        ("", ["README.md"])
    ],
    entry_points={}
)
