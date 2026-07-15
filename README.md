# Setup vscode
- users will need the extentions for vscode
- vscode environment has been setup in the .vscode folder
- use the command pallet `Ctrl+Shift+P` to:
    Project: Sync All Environments  (use on initial setup. Will make sure code can run)
    Project: Snapshot R Environment  (use on update. Will make sure dependencies are added to the environment)
    Project: Run Current R Script Background  (use to run R scripts)

# Setup python
- user should have uv installed (for users with an existing python run `pip install uv`)

# Integration with R
The desire for integration with R was explored but there was not enough time to get this working well. Instructions for R setup in VSCODE include:
- install the R extention
- you need to point vscode to the R instalation. On some environments this causes problems.
- Try to maintain good sepperation of concerns. In this project for example, the utilities are saved in a package under src, notebooks are saved in notebooks, data is saved in data. A good suggestion is to save R code in an `R` directory in this repo.

## Features
- **Download data from fingertips!** The `fingertips.py` script is a high performance downloader for the latest csv files for a single indicator. It saves the files locally and checks for updates every time you call the function. Most users will use the synchronous functions in scripts to avoid the aditional complexity of writing and debugging asynchronous code. The asynchronous functions can be used in ipynb's. The examples.ipynb notebook should be sufficient to explain the useage.
- **Store data sensibly!** Data is stored in a sensible structure mimicing the first layer of a medalion architecture. the directory structure is `data/{source}/{processing}/{partitions}/{dated_files}` where partitions are sensible ways to split up the data from source. for fingertips it makes sense to sepperatethe data by indicator_id. each file inside a partition reflects the data versioning history for that data source. For example, if the schema changes after 20270508, you can see the history of how the data has changed. 
- **Create generic plotting functions!** Given the data across fingertips requires unique analysis for each indicator id, the user will need to define the input data for the visualisations. The functions raise errors if the data is not in the correct format (ie, more than 1 comparator, duplicated values, missing columns). See the examples.ipynb file for examples of what minimal processing is typically required.
