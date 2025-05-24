#!/bin/bash

# OCR Command
# python main.py ocr -dc date -nc city -nz zoning -nd document

# Extract pages Command
# python main.py extract-pages -nc name_city -nd name_document

# Lille
# Extract pages
python main.py extract-pages -nc lille -nd zones_constructibles
python main.py extract-pages -nc lille -nd zones_inconstructibles
python main.py extract-pages -nc lille -nd zones_specifiques

# Bordeaux
# OCR w/ zoning (no Extract pages needed)
for date in data/external/bordeaux/*; do
    for zoning in data/external/bordeaux/$date/*; do
        for document in data/external/bordeaux/$date/$zoning/*; do
            python main.py ocr -dc $date -nc bordeaux -nz $zoning -nd "$document"
        done
    done
done

# Nantes
# OCR
python main.py ocr -dc 2023-12-15 -nc nantes -nd plu_general
# Extract pages
python main.py extract-pages -nc nantes -nd plu_general

