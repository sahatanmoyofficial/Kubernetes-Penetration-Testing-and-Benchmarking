from setuptools import setup,find_packages

with open("requirements.txt") as f:
    requirements = f.read().splitlines()

setup(
    name="Kubernetes-Penetration-Testing-and-Benchmarking",
    version="0.1",
    author="Tanmoy Saha",
    packages=find_packages(),
    install_requires = requirements,
)