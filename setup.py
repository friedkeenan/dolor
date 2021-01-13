import setuptools
import dolor

with open("README.md") as f:
    long_description = f.read()

setuptools.setup(
    name                          = "dolor",
    version                       = dolor.__version__,
    author                        = "dolor authors",
    description                   = "An asyncio Minecraft networking library",
    long_description              = long_description,
    long_description_content_type = "text/markdown",
    url                           = "https://github.com/friedkeenan/dolor",
    packages                      = setuptools.find_packages(),
    classifiers                   = [
        "Programming Language :: Python:: 3",
        "License :: OSI Approved :: ISC License (ISCL)",
        "Operating System :: OS Independent",
    ],
    python_requires               = ">=3.7",
)
