# FOLIO Migration Tools
![example workflow](https://github.com/FOLIO-FSE/MARC21-To-FOLIO/actions/workflows/python-app.yml/badge.svg)[![codecov](https://codecov.io/gh/FOLIO-FSE/folio_migration_tools/branch/main/graph/badge.svg?token=ZQL5ILWWGT)](https://codecov.io/gh/FOLIO-FSE/folio_migration_tools)   [![readthedocs](https://readthedocs.org/projects/docs/badge/?version=latest)](https://folio-migration-tools.readthedocs.io/)

A toolkit that enables you to migrate data over from a legacy ILS system into [FOLIO LSP](https://www.folio.org/)

# What is it good for?
FOLIO Migration tools enables you to migrate libraries with the most common ILS:s over to FOLIO without data losses or any major data transformation tasks. 
The tools transforms and loads the data providing you and the library with good actionable logs and data cleaning task lists together with the migrated data.

## What data does it cover?
FOLIO Migration Tools currently covers the following data sets:
* Catalog (Inventory and SRS in FOLIO terminology)
* Circulation transactions (Open loans and requests)
* Users/Patrons (In FOLIO, these share the same app/database)
* Courses and Reserves (Course reserves)
* Organizations (Vendor records)
* Orders (limited support)

### What additional functionality is on the roadmap?
This is the loose roadmap, in order of most likely implementations first
* ERM-related objects
* Financial records

### Can I use the tools for ongoing imports and integrations?
The tools are primarliy maintained for performing initial data migrations. We recommend that you use native FOLIO functionality for ongoing loads where possible. 
In theory, these tools can be used for ongoing patron loads from systems like Banner, Workday, or PeopleSoft. But we recommend you to weigh your options carefully before going down this path. 

# Contributing
Want to contribute? Read the [CONTRIBUTING.MD](https://github.com/FOLIO-FSE/folio_migration_tools/blob/main/CONTRIBUTING.md)

# Found an issue?
Report it on the [Github Issue tracker](https://github.com/FOLIO-FSE/folio_migration_tools/issues)

The scripts requires a FOLIO tenant with reference data properly set up. The script will throw messages telling what reference data is missing.
# Installing
Make sure you are running Python 3.9 or above. 
## 1. Using pip and venv
### 2.1. Create and activate a [virtual environment](https://packaging.python.org/en/latest/guides/installing-using-pip-and-virtual-environments/#creating-a-virtual-environment)   
```   
python -m venv ./.venv     # Creates a virtual env in the current folder
source .venv/bin/activate  # Activates the venv    
```
### 2. Install using pip: 
```
python -m pip install folio_migration_tools
```
### 3. Test the installation by showing the help pages 
```   
python -m folio_migration_tools -h
```    

## 2. Using pipenv
### 1. Run
```   
pipenv install folio-migration-tools
```   
### 2. Test the installation by showing the help pages
```  
pipenv run python3 -m folio_migration_tools -h
```  

# FOLIO migration process
This repo plays the main part in a process using a collection of tools. The process itself is documented in more detail, including example configuration files, at [this template repository](https://github.com/FOLIO-FSE/migration_repo_template)
In order to perform migrations according to this process, you need the following:
* An Installation of [FOLIO Migration Tools](https://pypi.org/project/folio-migration-tools/). Installation instructions above.
* A clone, or a separate repo created from [migration_repo_template](https://github.com/FOLIO-FSE/migration_repo_template)
* Access to the [Data mapping file creator](https://data-mapping-file-creator.folio.ebsco.com/data_mapping_creation) web tool
* A FOLIO tenant running the latest or the second latest version of FOLIO



# Running the scripts
For information on syntax, what files are needed and produced by the toolkit, refer to the documentation and example files in the [template repository](https://github.com/FOLIO-FSE/migration_repo_template). We are building out the docs section in this repository as well:[Documentation](https://folio-migration-tools.readthedocs.io/en/latest/)
¨
