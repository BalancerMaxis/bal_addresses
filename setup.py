from setuptools import setup, find_packages

VERSION = "0.9.15"
DESCRIPTION = "Balancer Maxi Addressbook"
LONG_DESCRIPTION = "Balancer Maxi Addressbook and Balancer Permissions helper"

# Setting up
setup(
    name="bal_addresses",
    version=VERSION,
    author="The Balancer Maxis",
    author_email="<nospam@balancer.community>",
    description=DESCRIPTION,
    long_description=LONG_DESCRIPTION,
    packages=find_packages(),
    include_package_data=True,  # Automatically include non-Python files
    package_data={"": ["abis/*.json"]},
    url="https://github.com/BalancerMaxis/bal_addresses",
    install_requires=[
        "bal_tools @ git+https://github.com/BalancerMaxis/bal_tools.git@fix/pin-web3-eth-brownie",
        "setuptools>=42",
        "wheel",
    ],
    keywords=["python", "first package"],
    classifiers=[
        "Development Status :: 4 - Beta",
        "Programming Language :: Python :: 3.9",
        "Operating System :: MacOS :: MacOS X",
        "Operating System :: Microsoft :: Windows",
        "Operating System :: Linux",
    ],
)
