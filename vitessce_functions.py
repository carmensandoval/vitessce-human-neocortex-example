import os
import json
from urllib.parse import quote_plus
from os.path import join
from anndata import AnnData
import scanpy as sc
import pandas as pd
import numpy as np
import boto3

from vitessce import (
    VitessceWidget,
    VitessceConfig,
    Component as cm,
    CoordinationType as ct,
    AnnDataWrapper,
)

# FUNCTIONS //////////////////////////////////////////////////////////////////

## Build anndata object
def buildAnnData(df):
    X = df[df.columns.values.tolist()[3:]].values
    X_spatial = df[["nucleus_x", "nucleus_y"]].values.astype('uint16')
    obs = pd.DataFrame(index = df.index.values.tolist())
    var = pd.DataFrame(index = df.columns.values.tolist()[3:])
    adata = AnnData(X = X, obs = obs, var = var, obsm = { "X_spatial": X_spatial })
    return adata

# [OPTIONAL] Run dimensionality reduction or clustering methods with ScanPy.
def scanpyProcess(adata):
    sc.pp.normalize_total(adata)
    sc.pp.log1p(adata)
    sc.tl.tsne(adata)
    adata.obs.index = adata.obs.index.astype(str)
    return adata

## Create a Vitessce configuration
# For more details about how to use the `vitessce` Python package 
# please visit the documentation at https://vitessce.github.io/vitessce-python/.

def buildVitessceConfig(adata, area_name):
    vc = VitessceConfig("Developing human neocortex: gestational week 20")
    dataset = vc.add_dataset(area_name).add_object(
        # The`add_object()` function converts the AnnData data structure into a [Zarr]
        # (https://zarr.readthedocs.io/en/stable/) store that is compatible with Vitessce.
        AnnDataWrapper(
            adata,
            mappings_obsm = ["X_tsne"],
            mappings_obsm_names = ["t-SNE"],
            expression_matrix = "X",
            spatial_centroid_obsm = "X_spatial"
        )
    )
    spatial_plot = vc.add_view(dataset, cm.SPATIAL)
    tsne_plot = vc.add_view(dataset, cm.SCATTERPLOT, mapping = "t-SNE")
    heatmap = vc.add_view(dataset, cm.HEATMAP)
    genes_list = vc.add_view(dataset, cm.GENES)
    vc.layout((spatial_plot | tsne_plot) / (heatmap | genes_list))
    return vc

## Vitessce with local web server /////////////////////////////////////////////////////////////

# Start the local web server:
# In a terminal, `cd` into the `data` directory.
# Then, run `http-server` on port 3000 with this terminal command:

# ```sh
# http-server ./ --cors -p 3000
# ```

## Export  converted files to the `data` directory.

def saveLocal(vc, area_name):
    OUT_DIR = join("./data/processed/", area_name)
    BASE_URL = 'http://localhost:3000'

    os.makedirs(OUT_DIR)
    config_dict = vc.export(to = 'files', base_url = BASE_URL, out_dir = OUT_DIR)

    # Save the Vitessce configuration to a file.    
    with open(join(OUT_DIR, JSON_NAME), "w") as my_json_file:
        json.dump(config_dict, my_json_file)

    vitessce_url = f"http://vitessce.io/?url={BASE_URL}/{JSON_NAME}"
    print(vitessce_url)

# After running the notebook cell above, a link to `vitessce.io` will appear. 
# While the local HTTP server is running and serving the exported files in the `data` directory, 
# you can open this link in a web browser to view the Vitessce visualization.


## UPLOAD TO AWS ///////////////////////////////////////////////////////////////////////

# If you would like to make this visualization public on the web, you can copy the files in `data` 
# to a cloud storage provider such as AWS S3, Google Cloud Storage, or GitHub Pages: 
# http://beta.vitessce.io/docs/data-hosting/.

# To store your data in an AWS S3 bucket, make sure the bucket permissions and CORS settings match those here: 
# https://github.com/vitessce/vitessce/blob/keller-mark/docs/docs/docs/data-hosting.md#bucket-policy

# In a terminal, set the environment variables for the AWS S3 bucket:

# ```sh
# export AWS_ACCESS_KEY_ID=my_access_key_id
# export AWS_SECRET_ACCESS_KEY=my_secret_access_key
# export AWS_DEFAULT_REGION=us-east-1
# ```

# Note: these environment variables need to be set in the terminal before starting JupyterLab 
# with the `jupyter lab` terminal command. (So you may need to exit the notebook, run these 3 lines, 
# and then start the notebook again by running `jupyter lab`)

def uploadToAWS(vc, my_json, area_name):

    BUCKET_NAME = "second-trimester-neocortex" # Replace with your bucket name
    BUCKET_PREFIX = area_name # Replace with a file path prefix you would like to use for each dataset
    
    S3_BASE_URL = base_url = f"https://{BUCKET_NAME}.s3.amazonaws.com/{BUCKET_PREFIX}"
    vitessce_url = f"http://vitessce.io/?url={S3_BASE_URL}/{my_json}"
    print(vitessce_url)
    
    s3 = boto3.resource(
        service_name = 's3',
        aws_access_key_id = os.environ['AWS_ACCESS_KEY_ID'],
        aws_secret_access_key = os.environ['AWS_SECRET_ACCESS_KEY']
    )

    # Upload both the converted data files and the Vitessce configuration JSON file to the S3 bucket.   
    config_dict = vc.export(to = 'S3', s3 = s3, bucket_name = BUCKET_NAME, prefix = BUCKET_PREFIX)

    s3.Bucket(BUCKET_NAME).put_object(Key = f"{BUCKET_PREFIX}/{my_json}", 
    Body = json.dumps(config_dict).encode())

# RUN ALL /////////////////////////////////////////////////////////////////////

def createBrowserFromFile(dir_in, file_name):
    print(file_name)
    AREA_NAME = os.path.splitext(file_name)[0]
    print(AREA_NAME)
    JSON_FILE = f"vitessce_config_{AREA_NAME}.json"

    my_df = pd.read_csv(join(dir_in, file_name), index_col = 0)
    my_adata = buildAnnData(df = my_df)
    my_adata = scanpyProcess(adata = my_adata)
    my_vc = buildVitessceConfig(area_name = AREA_NAME, adata = my_adata)
    uploadToAWS(vc = my_vc, my_json = JSON_FILE, area_name = AREA_NAME)