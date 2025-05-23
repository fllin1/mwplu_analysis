# Dashboard : MWPLU

## Adding / Updating synthesis

### Organisation

**ID** : the combinaison `cities`, `zoning` and `zones` (later `typologies`)
**cities** : table for the cities
**zoning** : table for the zoning (depends on the `city_id`)
**zones** : table for the zones (depends on the `zoning_id`)
**metadata** :
    - date of the creation of the synthesis;
    - date of the source plu;
    - IP adress of the user;
    - account info of the user (mail, name at least);
    - links to the source documents;
    (- later will add a score of the synthesis = accuracy ?)

### Steps

1. You have **selectors** for the `cities`, `zoning` and `zones` :
   - For the `cities` selector, you can :
     1. select an already existing city;
     2. enter a new city;
   - For the `zoning` selector, you can :
     1. select an already existing zoning;
     2. enter a new zoning;
   - For the `zones` selector, you can :
     1. select an already existing zone;
     2. enter a new zone (*this should not be used as this task should be automated*);

2. Drag and drop to update the PLU, select a city (resp. city and zoning if the PLU are specific for each zoning), if it :
   - already exists :
     1. update the synthesis;
     2. update the metadata (date of the plu, links to the source documents...);
     3. create a backup of the synthesis;
     4. create a backup of the metadata;
   - do not exists :
     1. create a new synthesis;
     2. select if it is "dispositions_generales";
     3. choose an explicit name;
     4. create the metadata;

**THATS ALL !**
