from setuptools import setup, find_packages

VERSION = '0.8.5'
DESCRIPTION = 'Balancer Maxi Addressbook'
LONG_DESCRIPTION = 'Balancer Maxi Addressbook and Balancer Permissions helper'

# Setting up
setup(
    name="bal_addresses",
    version=VERSION,
    author="Tritium",
    author_email="<nope@email.com>",
    description=DESCRIPTION,
    long_description=LONG_DESCRIPTION,
    packages=find_packages(),
    url="https://github.com/BalancerMaxis/bal_addresses",
    install_requires=["setuptools>=42", "wheel", "munch", "web3"],  # add any additional packages that
    # needs to be installed along with your package. Eg: 'caer'

    keywords=['python', 'first package'],
    classifiers=[
        "Development Status :: 2 - Beta",
        "Programming Language :: Python :: 3.9",
        "Operating System :: MacOS :: MacOS X",
        "Operating System :: Microsoft :: Windows",
        "Operating System :: Linux :: Linux"
    ]
)