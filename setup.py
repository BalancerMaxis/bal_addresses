from setuptools import setup, find_packages

VERSION = '0.0.3'
DESCRIPTION = 'Balancer Maxi Monorepo Addressbook'
LONG_DESCRIPTION = 'Balancer Maxi Monorepo Addressbook'

# Setting up
setup(
    name="bal_addresses",
    version=VERSION,
    author="Tritium",
    author_email="<nope@email.com>",
    description=DESCRIPTION,
    long_description=LONG_DESCRIPTION,
    packages=find_packages(),
    python_requires="==3.9",
    url="https://github.com/BalancerMaxis/bal-maxi-addresses",
    install_requires=["pandas", "pathlib"],  # add any additional packages that
    # needs to be installed along with your package. Eg: 'caer'

    keywords=['python', 'first package'],
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Programming Language :: Python :: 3.9",
        "Operating System :: MacOS :: MacOS X",
        "Operating System :: Microsoft :: Windows",
    ]
)