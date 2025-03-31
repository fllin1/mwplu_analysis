<a id="readme-top"></a>
<h1 align="center">Analyse PLU</h1>

The project PLU was built with

![Google Gemini](https://img.shields.io/badge/google%20gemini-8E75B2?style=for-the-badge&logo=google%20gemini&logoColor=white)
![Python](https://img.shields.io/badge/python-3670A0?style=for-the-badge&logo=python&logoColor=ffdd54)

- [About The Project](#about-the-project)
- [Installation](#installation)
- [Data Oraganization](#data-oraganization)
- [Back End](#back-end)
  - [OCR](#ocr)
  - [Format Data](#format-data)
  - [Analyse](#analyse)
- [Front End](#front-end)
- [Project Organization](#project-organization)


# About The Project

This project offers an end-to-end solution for automated document management that handles extraction, analysis, and synthesis of document data. Using API calls including Mistral OCR and Gemini-pro, the system processes both text and images to generate synthesis according to a template from unstructured documents.

**Key features include:**
- Automated document processing
- Combined text and image analysis
- Summarization according to a template
- Location-based document synthesis
- Cloud storage integration (TODO)
- User-friendly front-end access (TODO)

<p align="right">(<a href="#readme-top">back to top</a>)</p>

# Installation

1. Clone the repo
   ```sh
   git clone https://github.com/fllin1/plu.git
   ```
2. Install NPM packages
   ```sh
   pip install -r requirements.txt
   ```
3. Create and add your Google AI and Mistral API in `.env`
   ```
   MISTRAL_API_KEY = 'ENTER YOUR MISTRAL API KEY'
   GOOGLE_AI_API_KEY = 'ENTER YOUR MISTRAL API KEY'
   ```
4. Change git remote url to avoid accidental pushes to base project
   ```sh
   git remote set-url origin github_username/repo_name
   git remote -v # confirm the changes
   ```

<p align="right">(<a href="#readme-top">back to top</a>)</p>

# Data Oraganization

1. Create a folder for your city or specific zone in the `./data/external/` folder.
2. Place your document files with this kind of architectures:
```
city
  ├── zones_urbaines            <- Folder with the PLU
  │   ├── zone_UA1              <- PLU of the zones you want to analyse
  │   └── zone_UA2              <- You can put as many as you have
  ├── zones_urbaines            <- PLU for all the zones urbaines, you have to use the exact same name as your folder above
  ├── dispositions_generales    <- Disposition générales
  └── other_documents           <- Add the OAP and PPRI
```
3. You will need to reproduce this architecture in the `./config/plu_tree.yaml` file while separing the general documents and the specific documents for zones as such :
```yaml
city:
  documents_generaux:
    - dispositions_generales
    - other_documents
  documents_par_zone:
    zones_urbaines:
      - zone_UA1
      - zone_UA2
```

<p align="right">(<a href="#readme-top">back to top</a>)</p>

# Back End

## OCR

This part aims to extract all your `./data/external/{city}/` into the `./data/raw/{city}/` folder as `.json` files.

Analysing with Mistral OCR. Note that you will have to put credits in your Mistral account.
```sh
python src/orc.py --folder {city}
```
It saves all the full raw OCR responses and reproduces the folder structure in input.

<p align="right">(<a href="#readme-top">back to top</a>)</p>

## Format Data

Be careful, if Mistral OCR changes its output format, the preprocessing might not work.

This time, all the data will be combined in a single file as `./data/interim/data_{city}.json`.
```sh
python src/format.py --folder {city} --model-name "gemini-2.5-pro-exp-03-25"
```

<p align="right">(<a href="#readme-top">back to top</a>)</p>

## Analyse

<p align="right">(<a href="#readme-top">back to top</a>)</p>

# Front End

Analyse PLU

<p align="right">(<a href="#readme-top">back to top</a>)</p>

# Project Organization

```
├── LICENSE            <- Open-source license if one is chosen
├── Makefile           <- Makefile with convenience commands like `make data` or `make train`
├── README.md          <- The top-level README for developers using this project.
├── data
│   ├── external       <- Data from third party sources.
│   ├── interim        <- Intermediate data that has been transformed.
│   ├── processed      <- The final, canonical data sets for modeling.
│   └── raw            <- The original, immutable data dump.
│
├── docs               <- A default mkdocs project; see www.mkdocs.org for details
│
├── models             <- Trained and serialized models, model predictions, or model summaries
│
├── notebooks          <- Jupyter notebooks. Naming convention is a number (for ordering),
│                         the creator's initials, and a short `-` delimited description, e.g.
│                         `1.0-jqp-initial-data-exploration`.
│
├── pyproject.toml     <- Project configuration file with package metadata for 
│                         src and configuration for tools like black
│
├── references         <- Data dictionaries, manuals, and all other explanatory materials.
│
├── reports            <- Generated analysis as HTML, PDF, LaTeX, etc.
│   └── figures        <- Generated graphics and figures to be used in reporting
│
├── requirements.txt   <- The requirements file for reproducing the analysis environment, e.g.
│                         generated with `pip freeze > requirements.txt`
│
├── setup.cfg          <- Configuration file for flake8
│
└── src   <- Source code for use in this project.
    │
    ├── __init__.py             <- Makes src a Python module
    │
    ├── config.py               <- Store useful variables and configuration
    │
    ├── dataset.py              <- Scripts to download or generate data
    │
    ├── features.py             <- Code to create features for modeling
    │
    ├── modeling                
    │   ├── __init__.py 
    │   ├── predict.py          <- Code to run model inference with trained models          
    │   └── train.py            <- Code to train models
    │
    └── plots.py                <- Code to create visualizations
```

--------

<p align="right">(<a href="#readme-top">back to top</a>)</p>