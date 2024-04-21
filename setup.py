from setuptools import setup, find_packages

VERSION = "0.9.2"
DESCRIPTION = "Balancer Maxi Addressbook"
LONG_DESCRIPTION = "Balancer Maxi Addressbook and Balancer Permissions helper"

# Setting up
setup(
    name="bal_addresses",
    version=VERSION,
    author="Tritium",
    author_email="<nospam@balancer.community>",
    description=DESCRIPTION,
    long_description=LONG_DESCRIPTION,
    packages=find_packages(),
    include_package_data=True,  # Automatically include non-Python files
    package_data={"": ["graphql/**/*.gql", "abis/*.json"]},
    url="https://github.com/BalancerMaxis/bal_addresses",
    install_requires=[
        "setuptools>=42",
        "wheel",
        "munch==4.0.0",
        "web3",
        "gql",
        "requests",
    ],
    keywords=["python", "first package"],
    classifiers=[
        "Development Status :: 4 - Beta",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Operating System :: MacOS :: MacOS X",
        "Operating System :: Microsoft :: Windows",
        "Operating System :: Linux",
    ],
)
