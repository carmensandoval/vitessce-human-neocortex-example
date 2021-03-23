# vitessce-human-neocortex-example

## Setup

Create the conda environment and install the Python dependencies

```sh
conda env create -f environment.yml
```

Install [http-server](https://github.com/http-party/http-server#installation) (with homebrew if using Mac).

## Move data files to the `data` directory

Move `CellByFeature_Matrix.csv` to `data/CellByFeature_Matrix.csv`.

## Run the notebook

Activate the conda environment, then start JupyterLab and open the `process_data_for_vitessce.ipynb` Jupyter notebook.

```sh
conda activate vitessce-human-neocortex-env

jupyter lab
```
