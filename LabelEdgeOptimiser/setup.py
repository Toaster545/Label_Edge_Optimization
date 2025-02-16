from setuptools import setup, find_packages

# Read dependencies from requirements.txt
with open("requirements.txt") as f:
    required_packages = f.read().splitlines()

setup(
    name="LabelEdgeOptimiser",
    version="1.0.0",
    description="A LabelEdge optimisation application for efficient roll usage",
    author="Your Name",
    author_email="your.email@example.com",
    url="https://github.com/yourusername/LabelEdgeOptimiser",  # Update with your GitHub repo if applicable
    packages=find_packages(),
    install_requires=required_packages,  # Automatically loads dependencies
    entry_points={
        "console_scripts": [
            "labeledge=main:main",  # Run `labeledge` to start the app
        ],
    },
    include_package_data=True,
    package_data={
        "": ["*.qss", "*.ini"],  # Ensures non-code files are included
    },
    classifiers=[
        "Programming Language :: Python :: 3",
        "Operating System :: OS Independent",
    ],
    python_requires=">=3.6",
)
