import setuptools

config = {
    "author": "John Clary",
    "author_email": "john.clary@austintexas.gov",
    "classifiers": [
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "License :: Public Domain",
        "Programming Language :: Python :: 3",
    ],
    "description": "Integration services for ATD's knack applications.",
    "long_description_content_type": "text/markdown",
    "install_requires": ["arrow", "boto3", "knackpy", "sodapy"],
    "keywords": "knack api integration python",
    "license": "Public Domain",
    "name": "atd-knack-services",
    "packages": ["services"],
    "url": "http://github.com/cityofaustin/atd-knack-services",
    "version": "0.0.1",
}

if __name__ == "__main__":
    setuptools.setup(**config)
