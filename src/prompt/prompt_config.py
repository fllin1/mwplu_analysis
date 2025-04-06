# -*- coding: utf-8 -*-
"""Response schema for API Calls with Google GENAI API

This module defines the response schema for extracting pages of each zone
from the Réglement des Zones of the PLU (Plan Local d'Urbanisme).
It includes the configuration for generating content in different formats
such as text and JSON.

Version: 1.0
Date: 2025-03-31
Author: Grey Panda
"""

from google import genai
from google.genai import types


# Simple Text config for any task
CONFIG_DEFAULT: types.GenerateContentConfig = types.GenerateContentConfig(
    response_mime_type="text/plain",
)

# Json config for the json output format to extract the pages
# of each zone from the Réglement des Zones of the PLU.
CONFIG_EXTRACT_PAGES: types.GenerateContentConfig = types.GenerateContentConfig(
    response_mime_type="application/json",
    response_schema=genai.types.Schema(
        type=genai.types.Type.OBJECT,
        required=["response"],
        properties={
            "response": genai.types.Schema(
                type=genai.types.Type.ARRAY,
                items=genai.types.Schema(
                    type=genai.types.Type.OBJECT,
                    required=["zone", "pages"],
                    properties={
                        "zone": genai.types.Schema(
                            type=genai.types.Type.ARRAY,
                            items=genai.types.Schema(
                                type=genai.types.Type.STRING,
                            ),
                        ),
                        "pages": genai.types.Schema(
                            type=genai.types.Type.ARRAY,
                            items=genai.types.Schema(
                                type=genai.types.Type.INTEGER,
                            ),
                        ),
                    },
                ),
            ),
        },
    ),
)

# Json config for the json output of the template
CONFIG_TEMPLATE: types.GenerateContentConfig = types.GenerateContentConfig(
    response_mime_type="application/json",
    response_schema=genai.types.Schema(
        type=genai.types.Type.OBJECT,
        required=["DISPOSITION GENERALES"],
        properties={
            "DISPOSITION GENERALES": genai.types.Schema(
                type=genai.types.Type.OBJECT,
                required=[
                    "CHAPITRE 1 - DESTINATION DES CONSTRUCTIONS, USAGE DES SOLS, ACTIVITÉS ET INSTALLATIONS, MIXITÉ FONCTIONNELLE ET SOCIALE",
                    "CHAPITRE 2 - CARACTÉRISTIQUES URBAINES, ARCHITECTURALES, ENVIRONNEMENTALES ET PAYSAGÈRES",
                    "CHAPITRE 3 - EQUIPEMENTS ET RÉSEAUX",
                ],
                properties={
                    "CHAPITRE 1 - DESTINATION DES CONSTRUCTIONS, USAGE DES SOLS, ACTIVITÉS ET INSTALLATIONS, MIXITÉ FONCTIONNELLE ET SOCIALE": genai.types.Schema(
                        type=genai.types.Type.ARRAY,
                        items=genai.types.Schema(
                            type=genai.types.Type.OBJECT,
                            required=[
                                "1 - CONSTRUCTIONS, USAGES ET AFFECTATIONS DES SOLS, ACTIVITÉS ET INSTALLATIONS INTERDITS ",
                                "2 - CONSTRUCTIONS, USAGES ET AFFECTATIONS DES SOLS, ACTIVITÉS ET INSTALLATIONS SOUMISES À CONDITIONS PARTICULIÈRES ",
                                "3 - MIXITÉ FONCTIONNELLE ET SOCIALE ",
                            ],
                            properties={
                                "1 - CONSTRUCTIONS, USAGES ET AFFECTATIONS DES SOLS, ACTIVITÉS ET INSTALLATIONS INTERDITS ": genai.types.Schema(
                                    type=genai.types.Type.ARRAY,
                                    items=genai.types.Schema(
                                        type=genai.types.Type.OBJECT,
                                        required=[
                                            "1.1. CONSTRUCTIONS INTERDITES ",
                                            "1.2. USAGES ET AFFECTATIONS DES SOLS INTERDITS ",
                                            "1.3. ACTIVITÉS ET INSTALLATIONS INTERDITES",
                                        ],
                                        properties={
                                            "1.1. CONSTRUCTIONS INTERDITES ": genai.types.Schema(
                                                type=genai.types.Type.ARRAY,
                                                items=genai.types.Schema(
                                                    type=genai.types.Type.STRING,
                                                ),
                                            ),
                                            "1.2. USAGES ET AFFECTATIONS DES SOLS INTERDITS ": genai.types.Schema(
                                                type=genai.types.Type.ARRAY,
                                                items=genai.types.Schema(
                                                    type=genai.types.Type.STRING,
                                                ),
                                            ),
                                            "1.3. ACTIVITÉS ET INSTALLATIONS INTERDITES": genai.types.Schema(
                                                type=genai.types.Type.ARRAY,
                                                items=genai.types.Schema(
                                                    type=genai.types.Type.STRING,
                                                ),
                                            ),
                                        },
                                    ),
                                ),
                                "2 - CONSTRUCTIONS, USAGES ET AFFECTATIONS DES SOLS, ACTIVITÉS ET INSTALLATIONS SOUMISES À CONDITIONS PARTICULIÈRES ": genai.types.Schema(
                                    type=genai.types.Type.ARRAY,
                                    items=genai.types.Schema(
                                        type=genai.types.Type.OBJECT,
                                        required=[
                                            "2.1. CONSTRUCTIONS SOUMISES À DES CONDITIONS PARTICULIÈRES ",
                                            "2.2. USAGES ET AFFECTATIONS DES SOLS SOUMIS À DES CONDITIONS PARTICULIÈRES ",
                                            "2.3. ACTIVITÉS ET INSTALLATIONS SOUMISES À DES CONDITIONS PARTICULIÈRES",
                                        ],
                                        properties={
                                            "2.1. CONSTRUCTIONS SOUMISES À DES CONDITIONS PARTICULIÈRES ": genai.types.Schema(
                                                type=genai.types.Type.ARRAY,
                                                items=genai.types.Schema(
                                                    type=genai.types.Type.STRING,
                                                ),
                                            ),
                                            "2.2. USAGES ET AFFECTATIONS DES SOLS SOUMIS À DES CONDITIONS PARTICULIÈRES ": genai.types.Schema(
                                                type=genai.types.Type.ARRAY,
                                                items=genai.types.Schema(
                                                    type=genai.types.Type.STRING,
                                                ),
                                            ),
                                            "2.3. ACTIVITÉS ET INSTALLATIONS SOUMISES À DES CONDITIONS PARTICULIÈRES": genai.types.Schema(
                                                type=genai.types.Type.ARRAY,
                                                items=genai.types.Schema(
                                                    type=genai.types.Type.STRING,
                                                ),
                                            ),
                                        },
                                    ),
                                ),
                                "3 - MIXITÉ FONCTIONNELLE ET SOCIALE ": genai.types.Schema(
                                    type=genai.types.Type.ARRAY,
                                    items=genai.types.Schema(
                                        type=genai.types.Type.OBJECT,
                                        required=[
                                            "3.1. DISPOSITIONS EN FAVEUR DE LA MIXITÉ COMMERCIALE ET FONCTIONNELLE",
                                            "3.2. RÈGLES DIFFÉRENCIÉES ENTRE REZ-DE-CHAUSSÉE ET ÉTAGES SUPÉRIEURS ",
                                            "3.3. DISPOSITIONS EN FAVEUR DE LA MIXITÉ SOCIALE",
                                        ],
                                        properties={
                                            "3.1. DISPOSITIONS EN FAVEUR DE LA MIXITÉ COMMERCIALE ET FONCTIONNELLE": genai.types.Schema(
                                                type=genai.types.Type.ARRAY,
                                                items=genai.types.Schema(
                                                    type=genai.types.Type.STRING,
                                                ),
                                            ),
                                            "3.2. RÈGLES DIFFÉRENCIÉES ENTRE REZ-DE-CHAUSSÉE ET ÉTAGES SUPÉRIEURS ": genai.types.Schema(
                                                type=genai.types.Type.ARRAY,
                                                items=genai.types.Schema(
                                                    type=genai.types.Type.STRING,
                                                ),
                                            ),
                                            "3.3. DISPOSITIONS EN FAVEUR DE LA MIXITÉ SOCIALE": genai.types.Schema(
                                                type=genai.types.Type.ARRAY,
                                                items=genai.types.Schema(
                                                    type=genai.types.Type.STRING,
                                                ),
                                            ),
                                        },
                                    ),
                                ),
                            },
                        ),
                    ),
                    "CHAPITRE 2 - CARACTÉRISTIQUES URBAINES, ARCHITECTURALES, ENVIRONNEMENTALES ET PAYSAGÈRES": genai.types.Schema(
                        type=genai.types.Type.ARRAY,
                        items=genai.types.Schema(
                            type=genai.types.Type.OBJECT,
                            required=[
                                "4 - IMPLANTATION ET VOLUMÉTRIE DES CONSTRUCTIONS ET DES INSTALLATIONS ",
                                "5 - QUALITÉ URBAINE, ARCHITECTURALE, ENVIRONNEMENTALE ET PAYSAGÈRE",
                                "6 - TRAITEMENT ENVIRONNEMENTAL ET PAYSAGER DES ESPACES NON BÂTIS, DES CONSTRUCTIONS ET DE LEURS ABORDS ",
                            ],
                            properties={
                                "4 - IMPLANTATION ET VOLUMÉTRIE DES CONSTRUCTIONS ET DES INSTALLATIONS ": genai.types.Schema(
                                    type=genai.types.Type.ARRAY,
                                    items=genai.types.Schema(
                                        type=genai.types.Type.OBJECT,
                                        required=[
                                            "4.1. IMPLANTATION PAR RAPPORT AUX VOIES ET EMPRISES PUBLIQUES ",
                                            "4.2. IMPLANTATION DES CONSTRUCTIONS PAR RAPPORT AUX LIMITES SÉPARATIVES ",
                                            "4.3. IMPLANTATION DES CONSTRUCTIONS LES UNES PAR RAPPORT AUX AUTRES SUR UNE MÊME PROPRIÉTÉ ",
                                            "4.4. EMPRISE AU SOL DES CONSTRUCTIONS ",
                                            "4.5. COEFFICIENT D’EMPRISE AU SOL MINIMUM ET HAUTEUR MINIMUM AU SEIN DES PÉRIMÈTRES D’INTENSIFICATION URBAINE ",
                                            "4.6. HAUTEUR DES CONSTRUCTIONS ET DES INSTALLATIONS",
                                        ],
                                        properties={
                                            "4.1. IMPLANTATION PAR RAPPORT AUX VOIES ET EMPRISES PUBLIQUES ": genai.types.Schema(
                                                type=genai.types.Type.ARRAY,
                                                items=genai.types.Schema(
                                                    type=genai.types.Type.STRING,
                                                ),
                                            ),
                                            "4.2. IMPLANTATION DES CONSTRUCTIONS PAR RAPPORT AUX LIMITES SÉPARATIVES ": genai.types.Schema(
                                                type=genai.types.Type.ARRAY,
                                                items=genai.types.Schema(
                                                    type=genai.types.Type.STRING,
                                                ),
                                            ),
                                            "4.3. IMPLANTATION DES CONSTRUCTIONS LES UNES PAR RAPPORT AUX AUTRES SUR UNE MÊME PROPRIÉTÉ ": genai.types.Schema(
                                                type=genai.types.Type.ARRAY,
                                                items=genai.types.Schema(
                                                    type=genai.types.Type.STRING,
                                                ),
                                            ),
                                            "4.4. EMPRISE AU SOL DES CONSTRUCTIONS ": genai.types.Schema(
                                                type=genai.types.Type.ARRAY,
                                                items=genai.types.Schema(
                                                    type=genai.types.Type.STRING,
                                                ),
                                            ),
                                            "4.5. COEFFICIENT D’EMPRISE AU SOL MINIMUM ET HAUTEUR MINIMUM AU SEIN DES PÉRIMÈTRES D’INTENSIFICATION URBAINE ": genai.types.Schema(
                                                type=genai.types.Type.ARRAY,
                                                items=genai.types.Schema(
                                                    type=genai.types.Type.STRING,
                                                ),
                                            ),
                                            "4.6. HAUTEUR DES CONSTRUCTIONS ET DES INSTALLATIONS": genai.types.Schema(
                                                type=genai.types.Type.ARRAY,
                                                items=genai.types.Schema(
                                                    type=genai.types.Type.STRING,
                                                ),
                                            ),
                                        },
                                    ),
                                ),
                                "5 - QUALITÉ URBAINE, ARCHITECTURALE, ENVIRONNEMENTALE ET PAYSAGÈRE": genai.types.Schema(
                                    type=genai.types.Type.ARRAY,
                                    items=genai.types.Schema(
                                        type=genai.types.Type.OBJECT,
                                        required=[
                                            "5.1. INSERTION DES CONSTRUCTIONS ET DES INSTALLATIONS DANS LEUR ENVIRONNEMENT ",
                                            "5.2. CARACTÉRISTIQUES ARCHITECTURALES DES FAÇADES ET TOITURES ",
                                            "5.3. CARACTÉRISTIQUES DES CLÔTURES ",
                                            "5.4. PRESCRIPTIONS RELATIVES AU PATRIMOINE BÂTI ET PAYSAGER À PROTÉGER, À CONSERVER, À RESTAURER, À METTRE EN VALEUR OU À REQUALIFIER",
                                        ],
                                        properties={
                                            "5.1. INSERTION DES CONSTRUCTIONS ET DES INSTALLATIONS DANS LEUR ENVIRONNEMENT ": genai.types.Schema(
                                                type=genai.types.Type.ARRAY,
                                                items=genai.types.Schema(
                                                    type=genai.types.Type.STRING,
                                                ),
                                            ),
                                            "5.2. CARACTÉRISTIQUES ARCHITECTURALES DES FAÇADES ET TOITURES ": genai.types.Schema(
                                                type=genai.types.Type.ARRAY,
                                                items=genai.types.Schema(
                                                    type=genai.types.Type.STRING,
                                                ),
                                            ),
                                            "5.3. CARACTÉRISTIQUES DES CLÔTURES ": genai.types.Schema(
                                                type=genai.types.Type.ARRAY,
                                                items=genai.types.Schema(
                                                    type=genai.types.Type.STRING,
                                                ),
                                            ),
                                            "5.4. PRESCRIPTIONS RELATIVES AU PATRIMOINE BÂTI ET PAYSAGER À PROTÉGER, À CONSERVER, À RESTAURER, À METTRE EN VALEUR OU À REQUALIFIER": genai.types.Schema(
                                                type=genai.types.Type.ARRAY,
                                                items=genai.types.Schema(
                                                    type=genai.types.Type.STRING,
                                                ),
                                            ),
                                        },
                                    ),
                                ),
                                "6 - TRAITEMENT ENVIRONNEMENTAL ET PAYSAGER DES ESPACES NON BÂTIS, DES CONSTRUCTIONS ET DE LEURS ABORDS ": genai.types.Schema(
                                    type=genai.types.Type.ARRAY,
                                    items=genai.types.Schema(
                                        type=genai.types.Type.OBJECT,
                                        required=[
                                            "6.1. OBLIGATIONS EN MATIÈRE DE RÉALISATION D’ESPACES LIBRES ET DE PLANTATIONS, D’AIRES DE JEUX ET DE LOISIRS ",
                                            "6.2. SURFACES VÉGÉTALISÉES OU PERMÉABLES ",
                                            "6.3. MAINTIEN OU REMISE EN ÉTAT DES CONTINUITÉS ÉCOLOGIQUES ",
                                            "6.4. GESTION DES EAUX PLUVIALES ET DU RUISSELLEMENT ",
                                            "6.5. AMÉNAGEMENT D’EMPLACEMENTS SPÉCIFIQUES DÉDIÉS À LA COLLECTE DES DÉCHETS MÉNAGERS ET ASSIMILÉS",
                                        ],
                                        properties={
                                            "6.1. OBLIGATIONS EN MATIÈRE DE RÉALISATION D’ESPACES LIBRES ET DE PLANTATIONS, D’AIRES DE JEUX ET DE LOISIRS ": genai.types.Schema(
                                                type=genai.types.Type.ARRAY,
                                                items=genai.types.Schema(
                                                    type=genai.types.Type.STRING,
                                                ),
                                            ),
                                            "6.2. SURFACES VÉGÉTALISÉES OU PERMÉABLES ": genai.types.Schema(
                                                type=genai.types.Type.ARRAY,
                                                items=genai.types.Schema(
                                                    type=genai.types.Type.STRING,
                                                ),
                                            ),
                                            "6.3. MAINTIEN OU REMISE EN ÉTAT DES CONTINUITÉS ÉCOLOGIQUES ": genai.types.Schema(
                                                type=genai.types.Type.ARRAY,
                                                items=genai.types.Schema(
                                                    type=genai.types.Type.STRING,
                                                ),
                                            ),
                                            "6.4. GESTION DES EAUX PLUVIALES ET DU RUISSELLEMENT ": genai.types.Schema(
                                                type=genai.types.Type.ARRAY,
                                                items=genai.types.Schema(
                                                    type=genai.types.Type.STRING,
                                                ),
                                            ),
                                            "6.5. AMÉNAGEMENT D’EMPLACEMENTS SPÉCIFIQUES DÉDIÉS À LA COLLECTE DES DÉCHETS MÉNAGERS ET ASSIMILÉS": genai.types.Schema(
                                                type=genai.types.Type.ARRAY,
                                                items=genai.types.Schema(
                                                    type=genai.types.Type.STRING,
                                                ),
                                            ),
                                        },
                                    ),
                                ),
                            },
                        ),
                    ),
                    "CHAPITRE 3 - EQUIPEMENTS ET RÉSEAUX": genai.types.Schema(
                        type=genai.types.Type.ARRAY,
                        items=genai.types.Schema(
                            type=genai.types.Type.OBJECT,
                            required=[
                                "7 - STATIONNEMENT ",
                                "8 - DESSERTE PAR LES VOIES PUBLIQUES ET PRIVÉES ",
                                "9 - DESSERTE PAR LES RÉSEAUX ",
                                "10 - ENERGIE ET PERFORMANCES ÉNERGÉTIQUES",
                            ],
                            properties={
                                "7 - STATIONNEMENT ": genai.types.Schema(
                                    type=genai.types.Type.ARRAY,
                                    items=genai.types.Schema(
                                        type=genai.types.Type.OBJECT,
                                        required=[
                                            "7.1. STATIONNEMENT DES VÉHICULES MOTORISÉS ",
                                            "7.2. STATIONNEMENT DES CYCLES",
                                        ],
                                        properties={
                                            "7.1. STATIONNEMENT DES VÉHICULES MOTORISÉS ": genai.types.Schema(
                                                type=genai.types.Type.ARRAY,
                                                items=genai.types.Schema(
                                                    type=genai.types.Type.STRING,
                                                ),
                                            ),
                                            "7.2. STATIONNEMENT DES CYCLES": genai.types.Schema(
                                                type=genai.types.Type.ARRAY,
                                                items=genai.types.Schema(
                                                    type=genai.types.Type.STRING,
                                                ),
                                            ),
                                        },
                                    ),
                                ),
                                "8 - DESSERTE PAR LES VOIES PUBLIQUES ET PRIVÉES ": genai.types.Schema(
                                    type=genai.types.Type.ARRAY,
                                    items=genai.types.Schema(
                                        type=genai.types.Type.OBJECT,
                                        required=["8.1. ACCÈS ", "8.2. VOIRIES"],
                                        properties={
                                            "8.1. ACCÈS ": genai.types.Schema(
                                                type=genai.types.Type.ARRAY,
                                                items=genai.types.Schema(
                                                    type=genai.types.Type.STRING,
                                                ),
                                            ),
                                            "8.2. VOIRIES": genai.types.Schema(
                                                type=genai.types.Type.ARRAY,
                                                items=genai.types.Schema(
                                                    type=genai.types.Type.STRING,
                                                ),
                                            ),
                                        },
                                    ),
                                ),
                                "9 - DESSERTE PAR LES RÉSEAUX ": genai.types.Schema(
                                    type=genai.types.Type.ARRAY,
                                    items=genai.types.Schema(
                                        type=genai.types.Type.OBJECT,
                                        required=[
                                            "9.1. ALIMENTATION EN EAU POTABLE ",
                                            "9.2. GESTION DES EAUX USÉES DOMESTIQUES ",
                                            "9.3. GESTION DES EAUX USÉES NON DOMESTIQUE ",
                                            "9.4. UTILISATION DU RÉSEAU D’EAUX PLUVIALES ",
                                            "9.5. RÉSEAUX ÉLECTRIQUES ET TÉLÉPHONIQUES ",
                                            "9.6. DÉPLOIEMENT DE LA FIBRE OPTIQUE",
                                        ],
                                        properties={
                                            "9.1. ALIMENTATION EN EAU POTABLE ": genai.types.Schema(
                                                type=genai.types.Type.ARRAY,
                                                items=genai.types.Schema(
                                                    type=genai.types.Type.STRING,
                                                ),
                                            ),
                                            "9.2. GESTION DES EAUX USÉES DOMESTIQUES ": genai.types.Schema(
                                                type=genai.types.Type.ARRAY,
                                                items=genai.types.Schema(
                                                    type=genai.types.Type.STRING,
                                                ),
                                            ),
                                            "9.3. GESTION DES EAUX USÉES NON DOMESTIQUE ": genai.types.Schema(
                                                type=genai.types.Type.ARRAY,
                                                items=genai.types.Schema(
                                                    type=genai.types.Type.STRING,
                                                ),
                                            ),
                                            "9.4. UTILISATION DU RÉSEAU D’EAUX PLUVIALES ": genai.types.Schema(
                                                type=genai.types.Type.ARRAY,
                                                items=genai.types.Schema(
                                                    type=genai.types.Type.STRING,
                                                ),
                                            ),
                                            "9.5. RÉSEAUX ÉLECTRIQUES ET TÉLÉPHONIQUES ": genai.types.Schema(
                                                type=genai.types.Type.ARRAY,
                                                items=genai.types.Schema(
                                                    type=genai.types.Type.STRING,
                                                ),
                                            ),
                                            "9.6. DÉPLOIEMENT DE LA FIBRE OPTIQUE": genai.types.Schema(
                                                type=genai.types.Type.ARRAY,
                                                items=genai.types.Schema(
                                                    type=genai.types.Type.STRING,
                                                ),
                                            ),
                                        },
                                    ),
                                ),
                                "10 - ENERGIE ET PERFORMANCES ÉNERGÉTIQUES": genai.types.Schema(
                                    type=genai.types.Type.ARRAY,
                                    items=genai.types.Schema(
                                        type=genai.types.Type.STRING,
                                    ),
                                ),
                            },
                        ),
                    ),
                },
            ),
        },
    ),
)
