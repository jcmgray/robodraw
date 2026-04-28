# Installation

`robodraw` is available on [pypi](https://pypi.org/project/robodraw/). While `robodraw` is pure python itself, the preferred way to install it is with [pixi](https://pixi.sh), which creates isolated and reproducible environments that can mix packages from [`conda-forge`](https://conda-forge.org/) (the default) and also [`pypi`](https://pypi.org/).

**Installing with `pixi` (preferred):**
```bash
pixi init robodraw-project
cd robodraw-project
pixi add --pypi robodraw
```

**Installing with `pip`:**
```bash
pip install robodraw
# or
uv pip install robodraw
```
It is recommended to use [`uv`](https://docs.astral.sh/uv/) to install and manage purely pypi based environments.


**Installing the latest version directly from github:**

If you want to checkout the latest version of features and fixes, you can
install directly from the github repository:
```bash
pip install -U git+https://github.com/jcmgray/robodraw.git
```

**Installing a local, editable development version:**

If you want to make changes to the source code and test them out, you can
install a local editable version of the package:
```bash
git clone https://github.com/jcmgray/robodraw.git
pip install --no-deps -U -e robodraw/
```
