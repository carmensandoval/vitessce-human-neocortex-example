import os
os.chdir("/home/csandoval/cse-phd/second-trimester/browser/vitessce")

import vitessce_functions as vf
# import importlib
# RUN //////////////////////////////////////////////////////////////////
# if __name__ == '__main__':
## Load the data
# os.chdir("~/Dropbox/vitessce-human-neocortex-example")

file_list = os.listdir("./cell_by_feature_matrices/")
print(file_list)

for file_name in file_list[3:]:
    vf.createBrowserFromFile(dir_in = "./cell_by_feature_matrices/", file_name = file_name)

