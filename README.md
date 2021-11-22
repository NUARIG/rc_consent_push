# REDCap eConsent Push

Dummy flask application to test how to use REDCap bookmarks to push eConsent into a receiving application like Study Tracker or NOTIS.

## Installation

1. Clone this repo

2. Load the dependencies. You can use [miniconda](https://docs.conda.io/en/latest/miniconda.html#) as a way to create a python environment with module dependencies. Since conda doesn't include all packages we will need to use pip as well. Unfortunately, the requirements files are difficult to mix so you will need to do this in two steps.

```bash
# Create a conda environment from the file
$ conda create -n myenv --file conda_env_nopip.txt

# Make sure you activate the environment otherwise pip
# will install the dependencies into your global system environment
$ conda activate myenv

# Install pip-based packages using the pip requirements file
$ pip install -r pip_requirements.txt
```
3. Create a local `instance/` directory to put instance-specific files like the configuration file for DB credentials
```bash
$ mkdir instance
$ cp application.cfg.example instance/application.cfg
```

4. Initialize the database. Running the following from the command line will create the schema in your postgresql database.

```bash
# Optional, if you want to nuke the current scheme
$ flask dropdb

# This needs to run every time you need to initialize or re-initialize your DB
$ flask initdb
```

## Running

You will need to tell Flask the name of the application by creating the proper environment variables. I typically have a bash script file that I run once whenever I need to start the application in the terminal from the proper conda environment. Here's an example:

```bash
#!/usr/bin/env bash

conda deactivate
conda activate myenv 
export FLASK_APP=rc_consent_push
export FLASK_ENV=development
```

Running the server should be easy from then on. 
```bash
$ flask run
```

You can stop it using `^C`