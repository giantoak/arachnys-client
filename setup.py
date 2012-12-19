from setuptools import setup


setup(
    name='arachnys-client',
    version='0.4',
    description='Python client library for the Arachnys api',
    author='David Buxton',
    author_email='david@arachnys.com',
    py_modules=['arachnys'],
    install_requires=['requests>=1.0.3'],
)
