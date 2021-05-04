import setuptools

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setuptools.setup(
    name="pdf417decoder",
    version="1.0.6",
    author="Sparkfish LLC",
    author_email="packages@sparkfish.com",
    description="A PDF417 barcode decoder",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/sparkfish/pdf417decoder",
    project_urls={
        "Bug Tracker": "https://github.com/sparkfish/pdf417decoder/issues",
    },
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: Other/Proprietary License",
        "Operating System :: OS Independent",
    ],
    package_dir={"": "src"},
    packages=setuptools.find_packages(where="src"),
    python_requires=">=3.7",    
    install_requires=[
        "numpy >= 1.20.1",
        "opencv-python >= 4.5.1.48",
    ],
)