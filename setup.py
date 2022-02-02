from setuptools import setup
import pathlib

here = pathlib.Path(__file__).parent.resolve()

setup(
    name='update_address',
    version='0.0.1',
    long_description="For ROR Curator Use Only. This library updates the ROR address from the corresponding geonames response",
    url='https://github.com/ror-community/update_address',
    packages=["update_geonames"],
    python_requires=">=3.7",
    install_requires=["requests=2.22.0"]
    license="MIT"
)