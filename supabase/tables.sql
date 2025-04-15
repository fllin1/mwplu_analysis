-- Version 1.2
-- Date: 2025-04-15
-- Author: Grey Panda

-- Table des villes
CREATE TABLE villes(
id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
nom VARCHAR(255) UNIQUE NOT NULL,
created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Table des zonages - LIÉE À UNE VILLE SPÉCIFIQUE
CREATE TABLE zonages(
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  nom VARCHAR(255) NOT NULL,
  description TEXT,
  ville_id UUID REFERENCES villes(id) ON DELETE NO ACTION,
  created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
  updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
  -- Un même nom de zonage peut exister dans différentes villes, mais doit être unique dans une ville donnée
  UNIQUE(nom, ville_id)
);

-- Table des zones - LIÉE AU ZONAGE
CREATE TABLE zones(
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  nom VARCHAR(255) NOT NULL,
  description TEXT,
  zonage_id UUID REFERENCES zonages(id) ON DELETE NO ACTION,
  created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
  updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
  -- Un même nom de zone peut exister pour différents types de zones, mais doit être unique pour un type de zone donné
  UNIQUE(nom, zonage_id)
);

-- Table des typologies 
CREATE TABLE typologies(
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  nom VARCHAR(255) NOT NULL,
  description TEXT,
  created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
  updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
)

-- Table principale des documents
CREATE TABLE documents (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  -- Notez que nous n'avons pas besoin de ville_id ici car il est déjà inclus via zonage_id
  zonage_id UUID REFERENCES zonages(id) ON DELETE NO ACTION,
  zone_id UUID REFERENCES zones(id) ON DELETE NO ACTION,
  typologie_id UUID REFERENCES typologies(id) ON DELETE NO ACTION,
  content TEXT,
  plu_url VARCHAR(255),
  source_plu_date VARCHAR(255),
  created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
  updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
  -- Chaque combinaison doit être unique
  UNIQUE(zonage_id, zone_id, typologie_id)
);