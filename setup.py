import setuptools
import re
from pathlib import Path

projectroot = Path(__file__).parent.resolve()

# To incorporate README as long desription:
#
# Uncomment below and relevant line in setuptools.setup
with open("README.md", "r") as f:
    long_description = f.read()

# To include version number:
#
# Single source version number using nblabel/VERSION.txt
# Ensure that there is a MANIFEST.in file to include VERSION.txt in packaging
# Comment below:
# version = "0.1.0dev2"
# Uncomment below, and relevant line in setuptools.setup
# with open(projectroot / "nblabel/VERSION.txt", "r") as f:
#     version = f.read().strip()
versionfile = projectroot / "nblabel/__version.py"
with open(versionfile, "r") as f:
    line = f.read().strip()
find_ver = re.search('\\"(.*?)"', line)

if find_ver:
    version = find_ver.group(1)
else:
    raise RuntimeError("Version string not found in version file: %s" % versionfile)

setuptools.setup(
    # Important args
    name="nblabel",
    version=version,
    author="Tan Nian Wei",
    description="Label tabular data directly in Jupyter Notebook / Lab",
    packages=["nblabel"],
    install_requires=[
        "ipywidgets",
        "bqplot",
        "pandas",
        "numpy",
        "traitlets",
    ],  # SPECIFY DEPENDENCIES HERE e.g. ["pandas", "numpy"]
    # Less important args
    # author_email="YOUR-EMAIL-HERE",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/tnwei/nblabel",
    # python_requires=">=3.6", # SPECIFY REQUIRED PYTHON VERSION
    # include_package_data=True # Uncomment if using MANIFEST.in
)
