
from setuptools import setup, find_packages
setup(name="global-directory", version="3.0.0",
      packages=find_packages(), include_package_data=True,
      install_requires=["qrcode[pil]>=7.4.0","pillow>=9.0.0"],
      entry_points={"console_scripts":["global-directory=global_directory.cli:main"]})
