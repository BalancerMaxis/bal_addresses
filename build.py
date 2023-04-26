from setuptools import setup, find_packages

VERSION = '0.0.1'
DESCRIPTION = 'Balancer Maxi Monorepo Addressbook'
LONG_DESCRIPTION = 'Balancer Maxi Monorepo Addressbook'

# Setting up
setup(
    # the name must match the folder name 'verysimplemodule'
    name="balmaxi-addresses",
    version=VERSION,
    author="Tritium",
    author_email="<nope@email.com>",
    description=DESCRIPTION,
    long_description=LONG_DESCRIPTION,
    packages=find_packages(),
    install_requires=["pandas", "dotmap", "pathlib", "web3"],  # add any additional packages that
    # needs to be installed along with your package. Eg: 'caer'

    keywords=['python', 'first package'],
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: DeFi",
        "Programming Language :: Python :: 3.9",
        "Operating System :: MacOS :: MacOS X",
        "Operating System :: Microsoft :: Windows",
    ]
)