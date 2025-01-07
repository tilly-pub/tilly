import setuptools

with open("README.md", "r") as fh:
    long_description = fh.read()

setuptools.setup(
    name="tilly",
    version="0.0.1",
    author="Ronald Luitwieler",
    author_email="ronald.luitwieler@gmail.com",
    description="A cli for tracking Things I Learned (TIL)",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/orangewise/tilly",
    packages=setuptools.find_packages(),
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    python_requires=">=3.9",
)