# MWPLU Analysis

The project MWPLU Analysis was built with

![Python](https://img.shields.io/badge/python-3670A0?style=for-the-badge&logo=python&logoColor=ffdd54)
![Google Gemini](https://img.shields.io/badge/google%20gemini-8E75B2?style=for-the-badge&logo=google%20gemini&logoColor=white)
![Supabase](https://img.shields.io/badge/Supabase-181818?style=for-the-badge&logo=supabase&logoColor=white)

- [MWPLU Analysis](#mwplu-analysis)
  - [About The Project](#about-the-project)

## About The Project

This project offers an end-to-end solution for automated document management that handles extraction, analysis, and synthesis of document data. Using API calls including *Mistral OCR* and *Gemini*, the system processes both text and images to generate synthesis according to a template from unstructured documents.

Everything is then pushed and stored on the open-source database and storage solution Supabase.

**Key features include:**

- Optical Character Recognition
- Combined text and image analysis
- Summarization according to a template
- Supabase storage integration

[back to top](#mwplu-analysis)

1. Clone the repo

   ```sh
   git clone https://github.com/fllin1/plu.git
   ```

2. Create environement & Install packages

   *You might have to first install [pipx](https://pipx.pypa.io/stable/installation/).*

   The advised *Python version is 3.12*.
  
   ```sh
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

[Back to top](#mwplu-analysis)

