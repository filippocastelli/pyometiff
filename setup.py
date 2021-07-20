from setuptools import setup, find_packages
from pyometiff import __version__

with open("README.md", "r") as fh:
    long_description = fh.read()

setup(
    name="pyometiff",
    version=__version__,
    description="Read and Write OME-TIFFs in Python",
    packages=find_packages(exclude=("tests",)),
    # py_modules = ["omereader", "omewriter", "omexml"],
    # package_dir = {"": "pyometiff"},
    classifiers=[
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.6",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
        "License :: OSI Approved :: GNU General Public License v2 or later (GPLv2+)",
        # "Operating System :: Os Independent",
    ],
    long_description=long_description,
    long_description_content_type="text/markdown",
    install_requires=["numpy",
                      "tifffile>2020.10.1",
                      "imagecodecs",
                      "lxml"],
    extras_require={
        "dev": ["pytest>3.7", "mock"],
    },
    url="https://github.com/filippocastelli/pyometiff",
    author="Filippo Maria Castelli",
    author_email="castelli@lens.unifi.it",
)
