# Welcome to pooch-figshare

[![License](https://img.shields.io/badge/License-BSD%202--Clause-orange.svg)](https://opensource.org/licenses/BSD-2-Clause)
[![GitHub Workflow Status](https://img.shields.io/github/actions/workflow/status/pooch-figshare//ci.yml?branch=main)](https://github.com/pooch-figshare//actions/workflows/ci.yml)
[![Documentation Status](https://readthedocs.org/projects//badge/)](https://.readthedocs.io/)
[![codecov](https://codecov.io/gh/pooch-figshare//branch/main/graph/badge.svg)](https://codecov.io/gh/pooch-figshare/)

## Installation

The Python package `pooch_figshare` can be installed from PyPI:

```
python -m pip install pooch_figshare
```

## Development installation

If you want to contribute to the development of `pooch_figshare`, we recommend
the following editable installation from this repository:

```
git clone https://github.com/ssciwr/pooch-figshare/
cd pooch-figshare
python -m pip install --editable .[tests]
```

Having done so, the test suite can be run using `pytest`:

```
python -m pytest
```

## Acknowledgments

This repository was set up using the [SSC Cookiecutter for Python Packages](https://github.com/ssciwr/cookiecutter-python-package).
