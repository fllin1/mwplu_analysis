# Analyse PLU

Project PLU

- [Analyse PLU](#analyse-plu)
- [Automatic retrieval](#automatic-retrieval)
- [Extraction](#extraction)
  - [1. Extraction from pdf files](#1-extraction-from-pdf-files)
  - [2. Cleaning of useless text and images](#2-cleaning-of-useless-text-and-images)
    - [a. Text data](#a-text-data)
    - [b. Image data](#b-image-data)
- [Analyzing each document](#analyzing-each-document)
  - [1. Sending each extracted document for summarization](#1-sending-each-extracted-document-for-summarization)
  - [2. Storing the Data](#2-storing-the-data)
    - [a. Tagging and naming the documents](#a-tagging-and-naming-the-documents)
- [Synthesizing analysis](#synthesizing-analysis)
  - [1. Retrieval of all summary related to a location](#1-retrieval-of-all-summary-related-to-a-location)
  - [2. Synthesizing (Gemini or Qwen1M)](#2-synthesizing-gemini-or-qwen1m)
  - [3. Storing of synthesis](#3-storing-of-synthesis)
- [Front End](#front-end)
- [Project Organization](#project-organization)


The following plan follows the construction of the project.

# Automatic retrieval

<!-- TODO -->

# Extraction

If you download yout data manually, create a folder in `data/external` and place your files into it. You can create sub-folders at your convenience.

You have to setup your `.env` file, with your a `MISTRAL_API_KEY`.

## 1. Extraction from pdf files

With **Mistral OCR API**, simply use the terminal command: 

```zsh
python src/dataset.py extract-data -f folder_name
```

where `folder_name` of the data that you wish to extract.

All files will then be stored in the `data/raw/folder_name` folder, compromising individual folders for each original pdf file, with text data in a markdown format, and images in an /images folder.


## 2. Cleaning of useless text and images

### a. Text data

Cleans the markdown data.

### b. Image data

**Current Method:** Removes images based of the references in the `references/images` folder.

Run : 
```zsh 
python src/dataset.py clean-data -f folder_name
```


# Analyzing each document
   
## 1. Sending each extracted document for summarization


## 2. Storing the Data
   
### a. Tagging and naming the documents


### b. Storage on the cloud

# Synthesizing analysis
   
## 1. Retrieval of all summary related to a location

## 2. Synthesizing (Gemini or Qwen1M) 

## 3. Storing of synthesis


# Front End

Analyse PLU

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

