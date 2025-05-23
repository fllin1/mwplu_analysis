# Analyse PLU

The project PLU was built with

![Python](https://img.shields.io/badge/python-3670A0?style=for-the-badge&logo=python&logoColor=ffdd54)
![Google Gemini](https://img.shields.io/badge/google%20gemini-8E75B2?style=for-the-badge&logo=google%20gemini&logoColor=white)
![Supabase](https://img.shields.io/badge/Supabase-181818?style=for-the-badge&logo=supabase&logoColor=white)

- [Analyse PLU](#analyse-plu)
  - [About The Project](#about-the-project)
  - [Installation](#installation)
  - [Data Oraganization](#data-oraganization)
  - [Back End](#back-end)
    - [Step by step (decraped)](#step-by-step-decraped)
    - [Pipeline](#pipeline)
    - [Load Data](#load-data)
  - [Project Organization](#project-organization)

## About The Project

This project offers an end-to-end solution for automated document management that handles extraction, analysis, and synthesis of document data. Using API calls including Mistral OCR and Gemini-pro, the system processes both text and images to generate synthesis according to a template from unstructured documents.
Everything is then pushed and stored on the open-source database and storage solution Supabase.

**Key features include:**

- Automated document processing
- Combined text and image analysis
- Summarization according to a template
- Location-based document synthesis
- Cloud storage integration

[back to top](#analyse-plu)

## Installation

1. Clone the repo

   ```sh
   git clone https://github.com/fllin1/plu.git
   ```

2. Create environement & Install packages

   *You might have to first install [pipx](https://pipx.pypa.io/stable/installation/).*

   Then create at your conveniance either a python or a conda environment. The advised *Python version is 3.12*.
  
   ```sh
   conda create -n plu python=3.12
   conda activate plu
   pipx install poetry
   poetry install
   ```

3. Create and add your Google AI and Mistral API in `.env`

   ```text
   MISTRAL_API_KEY = 'ENTER YOUR MISTRAL API KEY'
   GOOGLE_AI_API_KEY = 'ENTER YOUR MISTRAL API KEY'
   SUPABASE_URL = 'ENTER YOUR SUPABASE URL'
   SUPABASE_KEY = 'ENTER YOUR SUPABASE API KEY'
   ```

4. Change git remote url to avoid accidental pushes to base project

   ```sh
   git remote set-url origin github_username/repo_name
   git remote -v # confirm the changes
   ```

[Back to top](#analyse-plu)

## Data Oraganization

1. Create a folder for your city or specific zone in the `./data/external/` folder.
2. Then place your documents/PLU in this folder, you can name them however you want, you will have to specify these file names again to run the code anyway :

   ```sh
   city
     ├── zones_urbaines            <- PLU for all the zones urbaines, you have to use the exact same name as your folder above
     ├── dispositions_generales    <- Disposition générales
     └── other_documents           <- Add the OAP and PPRI
   ```

3. You should reference your prompts in the references folders. As of now, only two prompts are used :
   1. The first being `./references/prompt_reglement_zone.txt` asking the LLM to specify which pages of a PLU refers to which "Zone" name.
   2. The second prompt is for the analysis `./references/prompt_plu.txt` and should contain the variable *{ZONE_CADASTRALE_CIBLE}*.

4. You will need to reproduce this architecture in the `./config/plu_tree.yaml` file while separing the general documents and the specific documents for zones as such :

```yaml
city:
  documents_generaux:
    - dispositions_generales
    - other_documents
  zones_urbaines:
    - zone_UA1
    - zone_UA2
```

**IMPORTANT** : The dependency between this format of the file and the below functions was not maintained, it might be broken. Unit tests will need to be created.

You should now use either the `main.py` function to run analysis over a single zone, or the `pipe.py` file to run multiple analysis.

[Back to top](#analyse-plu)

## Back End

The following sections will demonstrate how to run each part of the project independently, and the last part will show you how to run the pipeline of the project.

### Step by step (decraped)

1. **OCR**
  
   This part aims to extract all your `./data/external/{city}/` into the `./data/raw/{city}/` folder as `.json` files.

   Analysing with Mistral OCR. Note that you will have to put *credits* in your Mistral account.

   ```sh
   python src/dump/orc.py --folder {city}
   ```

   It saves all the full raw OCR responses and reproduces the folder structure in input.

   [Back to top](#analyse-plu)

2. **Format Data**

   Be careful, if Mistral OCR changes its output format, the preprocessing might not work.

   This time, all the data will be combined in a single file as `./data/interim/data_{city}.json`.

   ```sh
   python src/dump/format.py --folder {city} --model-name "gemini-2.5-pro-exp-03-25"
   ```

   [Back to top](#analyse-plu)

3. **Analysis**

   After completing the previous steps, you don't have much to do here.

   You can retrieve the Gemini output prompts here `./data/processed/data_{city}.json`.

   ```sh
   python src/dump/analyse.py --folder {city} --model-name "gemini-2.5-pro-exp-03-25"
   ```

   [Back to top](#analyse-plu)

### Pipeline

The pipeline is built on the `main.py` file, which comprises 2 functions. The first being the OCR function, which also runs the *retrieve_zone_pages* function. The second being the synthesis, which takes the OCR results, run the analysis and creates the final pdf file.

We then have the pipeline file which allows us to run this two parts on multiple files, you will have to fill the `./config/pipeline_config.json` before-end, by following the structure explained in the doctring of the `pipe.py` script.

[Back to top](#analyse-plu)

### Load Data

The last step is to load the data on our Supabase Database using the `./supabase/load_data.py` script.

**NOTE** : The pdf files will have to be placed in a bucket by hand for now, using the following structure,

- Bucket name: synthesis
- Root folders : {city_name}
- Children folders : {type_de_zone}
- Place the pdf files in the children folders

## Project Organization

```text
├── LICENSE            <- MIT License.
├── Makefile           <- Makefile (not used).
├── README.md          <- The top-level README for developers using this project.
├── data
│   ├── external       <- Original `.pdf` files.
│   ├── interim        <- Intermediate data that has been preprocessed.
│   ├── processed      <- The raw reponses analysis of each zone.
│   └── raw            <- The OCR raw responses.
│
├── docs               <- Documents of the project.
│
├── notebooks          <- Jupyter notebooks for testing.
│
├── pyproject.toml     <- Project configuration file with package metadata for src.
│
├── references         <- Text version of prompt for edits and conversion to json.
│
├── requirements.txt   <- The requirements files for the python analysis.
│
├── setup.cfg          <- Configuration file for flake8 (not used).
│
└── src   <- Source code for use in this project.
    │
    ├── api                
    │   ├── __init__.py 
    │   ├── gemini_thinking.py  <- Code for API calls to Gemini models.
    │   └── mistral_ocr.py      <- Code to train models.
    │
    ├── dump
    │   ├── analyse.py          <- Scripts to send prompts and retrieve analysis.
    │   ├── format.py           <- Scripts format using `src/static/preprocess.py`.
    │   └── orc.py              <- Code to use OCR on external `.pdf` files.
    │
    ├── prompt                
    │   ├── __init__.py 
    │   ├── prompt_config.py    <- Generation Content Configurations constant.
    │   └── txt_to_json.py      <- Code to convert prompts in `/references/` to `.json`.
    │
    ├── static                
    │   ├── __init__.py 
    │   ├── create_report.py    <- Code to create the reports from the JSON results.
    │   ├── pdf.py              <- Utility functions for pdfs.
    │   ├── preprocess.py       <- Code to preprocess raw OCR responses.
    │   └── prompt_format.py    <- Code to create prompts from preprocess data.
    │
    ├── __init__.py             <- Makes src a Python module.
    │
    ├── config.py               <- Store useful variables and configuration.
    │
    └── utils.py                <- Variety of useful fonctions.
```

--------

[Back to top](#analyse-plu)

Version : 0.1.2
Author : Grey Panda
