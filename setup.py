import setuptools

with open("README.md", "r") as fh:
    long_description = fh.read()

setuptools.setup(
    name="tilly",
    version="0.0.2",
    author="Ronald Luitwieler",
    author_email="ronald.luitwieler@gmail.com",
    description="A cli for tracking Things I Learned (TIL)",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/orangewise/tilly",
    packages=setuptools.find_packages(),
    install_requires=[
        "click>=8.0",
        "pluggy>=1.0",
        "setuptools"
    ],
    entry_points={
        "console_scripts": [
            "til = tilly.main:cli",
            "tilly = tilly.main:cli"
        ]
    },
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    python_requires=">=3.9",
)