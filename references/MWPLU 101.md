# Local : MWPLU Analysis

## 0-Rules

### A-Naming

- All folders and files names shall be **lowercase**;
- All leading or trailing spaces shall be removed;
- All *spaces* and *punctuations* shall be replaced by **underscores**;
- **No plurial** for any variable, file or folder name;
- For variables, always indicate the type first e.g. "path_file" where *path* is the type;

### B-Convention

Existing types :

- name
- path
- date
- number
- url

We'll always specify these three points :

1. Metadata e.g. file_path in the Supabase bucket;
2. Structure : the files and folders structure;
3. Data : the structure and type of the data (input and output if needed);

**IMPORTANT** : The information specified will always be the minimum amount of data required, additional information can be kept if wanted.

## I-Extract data from PLU

### A-External plu.pdf

Stored in the `/data/external/` folder, with pdf files that contain **text** and **images**.

Metadata (reference in a Supabase table):

- path_file_source_docuement;
- date_creation_source_document;

Three types of document and three cases for a city :

1. Multiple documents (dispositions_generales & zoning_documents);
2. Multiple documents (only zoning_documents);
3. Single document (general_plu);

```text
external/
├── city_1/
│   ├── disposition_generales.pdf
│   ├── zones_urbaines_mixtes.pdf
│   └── (...)
│
├── city_2/
│   ├── zones_dediees.pdf
│   └── (...)
│
├── city_3/
│   └── general_plu.pdf
```

### B-Optical Character Recognition

Output stored in the `/data/raw/` folder.

The metadata and the data structure : [OCR Output](/references/api/ocr_output.json).

In parallel, we'll have to create a python module to convert the output of each OCR model to the desired output, these scripts will be stored in the `./src/api/utils/` folder.
The python files name will be the name of the model used, and in the file docstring, the exact reference and version of the model from the last update of the file should be written.

We'll keep the input naming convention :

```text
raw/
├── city_1/
│   ├── disposition_generales.json
│   ├── zones_urbaines_mixtes.json
│   └── (...)
│
```

### C-Separate documents per zone

Output stored in the `/data/interim/` folder.

For this step, we'll divide the whole PLU into subfiles, for each zone + dispositions_generales if it exists.
After this step, we'll save the output on Supabase.

The metadata and the data structure : [Pages Output](/references/api/pages_output.json)

We'll create subfolders with input naming convention, and place our results in it :

```text
interim/
├── city_1/
│   ├── disposition_generales/
│   │   ├──
│   │   ├──

│   ├── zones_urbaines_mixtes/
│   └── (...)
│
```