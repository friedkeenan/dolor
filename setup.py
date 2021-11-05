import setuptools

# TODO: README.md as long_description

setuptools.setup(
    name            = "dolor",
    version         = "0.1.0",
    author          = "friedkeenan",
    description     = "An asyncio Minecraft networking library",
    url             = "https://github.com/friedkeenan/dolor",
    packages        = setuptools.find_packages(),

    classifiers = [
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: ISC License (ISCL)",
        "Operating System :: OS Independent",
    ],

    python_requires = ">= 3.7",
)
