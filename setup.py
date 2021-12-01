import pathlib
from setuptools import setup

HERE = pathlib.Path(__file__).parent

README = (HERE / "README.rst").read_text()

setup(
    name="ryca_django_grpc",
    version="1.0.13",
    description="Django gRPC framework",
    long_description=README,
    long_description_content_type="text/x-rst",
    url="https://github.com/realsaeedhassani/ryca-django-grpc",
    author="Saeed Hasani Borzadaran",
    author_email="hassanisaeed19@gmail.com",
    license="MIT",
    classifiers=["Environment :: Web Environment",
                 "Framework :: Django",
                 "Intended Audience :: Developers",
                 "Operating System :: OS Independent",
                 "Programming Language :: Python",
                 "Programming Language :: Python :: 3",
                 "Programming Language :: Python :: 3 :: Only",
                 "Programming Language :: Python :: 3.6",
                 "Programming Language :: Python :: 3.7",
                 "Programming Language :: Python :: 3.8",
                 ],
    include_package_data=True,
)
