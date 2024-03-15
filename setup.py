from setuptools import setup, find_packages

VERSION = '0.9.0'
DESCRIPTION = 'Balancer Maxi Addressbook'
LONG_DESCRIPTION = 'Balancer Maxi Addressbook and Balancer Permissions helper'

# Setting up
setup(
    name="bal_addresses",
    version=VERSION,
    author="Tritium",
    author_email="<nospam@balancer.community>",
    description=DESCRIPTION,
    long_description=LONG_DESCRIPTION,
    packages=find_packages(),
    package_data={
        'bal_addresses': ['graphql/*', 'abis/*'],
    },
    url="https://github.com/BalancerMaxis/bal_addresses",
    install_requires=["setuptools>=42", "wheel", "munch==4.0.0", "web3", "gql[requests]", "requests"],  # add any additional packages that
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

setup(
    name='your_package_name',
    version='1.0',
    packages=find_packages(),
    package_data={
        'your_package_name': ['subdirectory/*', 'subdirectory/*.txt', 'subdirectory/*.json'],
    },
    # Other setup configurations...
)