#from ez_setup import use_setuptools
#use_setuptools()
from setuptools import setup, find_packages


setup(
    name='exivfind',
    version="1.0",
    description="Extends pygnutools find with ability with primaries that "
    "various EXIF tags support",
    author="Meitham Jamaa",
    packages=find_packages(),
    include_package_data=True,
    install_requires=["pygnutools>=0.1"],
    entry_points="""
        [pygnutools.plugin]
        primaries=exivfind:primaries_map
        cli_args=exivfind:cli_args
    """,
)
