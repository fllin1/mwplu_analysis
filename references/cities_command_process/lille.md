# Pipeline de traitement PLU - Ville de Lille

Ce document décrit le processus complet de traitement des données PLU pour la ville de Lille, incluant les étapes spécifiques développées pour cette ville.

## Vue d'ensemble du pipeline

Le pipeline de traitement pour Lille comprend les étapes suivantes :

1. OCR des documents PDF
2. Extraction des pages par zones
3. Réorganisation des fichiers zones spécifiques
4. Ajout des métadonnées zones constructibles
5. Synthèse des données
6. Génération des rapports
7. Upload vers Supabase

## Étapes détaillées

### 1. OCR des documents PDF

**Description :** Conversion des documents PDF en texte structuré avec extraction des images et métadonnées.

```bash
python bulk_runner.py run --stages ocr --cities lille
```

### 2. Extraction des pages par zones

**Description :** Extraction et organisation des pages par zones selon les catégories définies dans les fichiers de configuration.

```bash
python bulk_runner.py run --stages extract_pages --cities lille
```

### 3. Réorganisation des fichiers zones spécifiques (Étape spécifique Lille)

**Description :** Déplacement des fichiers JSON des zones spécifiques vers un dossier dédié basé sur le fichier `zones_specifiques.json`.

```bash
python test/cities/lille/zones_specifiques.py
```

**Détails :**

- Lit le fichier `data/interim/lille/zones_specifiques.json`
- Déplace les fichiers de `data/interim/lille/{categorie_generale}/{code_zone}.json` vers `data/interim/lille/zones_specifiques/`
- 99 fichiers traités (zones urbaines et zones naturelles/forestières)

### 4. Ajout des métadonnées zones constructibles (Étape spécifique Lille)

**Description :** Ajout du champ `zones_constructibles` dans les métadonnées de tous les fichiers JSON de zones.

```bash
python test/cities/lille/zones_constructibles.py
```

**Détails :**

- Traite les fichiers référencés dans `zones_constructibles.json` → `zones_constructibles: true`
- Traite les fichiers référencés dans `zones_inconstructibles.json` → `zones_constructibles: false`
- 159 fichiers mis à jour au total

### 5. Synthèse des données

**Description :** Génération des fichiers de synthèse et consolidation des données extraites.

```bash
python bulk_runner.py run --stages synthesis --cities lille
```

### 6. Génération des rapports

**Description :** Création des rapports d'analyse et de statistiques sur les données traitées.

```bash
python bulk_runner.py run --stages reports --cities lille
```

### 7. Upload vers Supabase

**Description :** Upload des données traitées vers la base de données Supabase, incluant les métadonnées zones constructibles.

```bash
python bulk_runner.py run --stages upload_supabase --cities lille
```

## Pipeline complet automatisé

Pour exécuter l'ensemble du pipeline standard :

```bash
python bulk_runner.py run --all-stages --cities lille
```

**⚠️ Important :** Les étapes spécifiques Lille (3 et 4) doivent être exécutées manuellement entre les étapes 2 et 5.

## Pipeline complet avec étapes spécifiques Lille

```bash
# 1-2. OCR et extraction des pages
python bulk_runner.py run --stages ocr --stages extract_pages --cities lille

# 3. Réorganisation zones spécifiques (spécifique Lille)
python test/cities/lille/zones_specifiques.py

# 4. Ajout métadonnées constructibilité (spécifique Lille)
python test/cities/lille/zones_constructibles.py

# 5-7. Synthèse, rapports et upload
python bulk_runner.py run --stages synthesis --stages upload_supabase --cities lille
```

## Vérification du statut

Pour vérifier l'état d'avancement du pipeline :

```bash
python bulk_runner.py status --refresh
```

## Structure des données spécifiques Lille

### Fichiers de configuration

- `data/interim/lille/zones_specifiques.json` : Liste des zones spécifiques (99 zones)
- `data/interim/lille/zones_constructibles.json` : Zones constructibles (148 zones)
- `data/interim/lille/zones_inconstructibles.json` : Zones non constructibles (11 zones)

### Dossiers de sortie

- `data/interim/lille/zones_specifiques/` : Fichiers des zones spécifiques consolidés
- `data/interim/lille/Zones Urbaines/` : Zones urbaines restantes
- `data/interim/lille/Zones Naturelles et Forestières/` : Zones naturelles restantes
- `data/interim/lille/Zones Agricoles/` : Zones agricoles
- `data/interim/lille/Zones À Urbaniser/` : Zones à urbaniser

### Métadonnées ajoutées

Chaque fichier JSON de zone contient maintenant :

```json
{
  "metadata": {
    "zones_constructibles": true/false,
    // ... autres métadonnées
  }
}
```

## Dépannage

### Problèmes courants

1. **Fichiers manquants** : Vérifier que l'étape d'extraction des pages s'est bien déroulée
2. **Erreurs de métadonnées** : S'assurer que les fichiers JSON ont une structure `metadata` valide
3. **Problèmes d'upload** : Vérifier la configuration Supabase et les permissions

### Logs

Les logs détaillés sont disponibles dans le dossier `logs/` du projet.

## Notes importantes

- Les scripts spécifiques Lille sont idempotents (peuvent être exécutés plusieurs fois sans problème)
- La base de données Supabase doit avoir la colonne `zones_constructibles` dans la table `zones`
- Les étapes spécifiques doivent être exécutées dans l'ordre indiqué
