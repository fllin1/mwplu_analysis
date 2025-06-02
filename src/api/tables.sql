-- CITIES
CREATE TABLE
    cities (
        id uuid PRIMARY KEY DEFAULT uuid_generate_v4 (),
        name varchar UNIQUE NOT NULL,
        created_at timestamptz DEFAULT CURRENT_TIMESTAMP,
        updated_at timestamptz DEFAULT CURRENT_TIMESTAMP
    );

-- ZONINGS
CREATE TABLE
    zonings (
        id uuid PRIMARY KEY DEFAULT uuid_generate_v4 (),
        name varchar NOT NULL,
        description text,
        city_id uuid REFERENCES cities (id),
        created_at timestamptz DEFAULT CURRENT_TIMESTAMP,
        updated_at timestamptz DEFAULT CURRENT_TIMESTAMP
    );

-- ZONES
CREATE TABLE
    zones (
        id uuid PRIMARY KEY DEFAULT uuid_generate_v4 (),
        name varchar NOT NULL,
        description text,
        zoning_id uuid REFERENCES zonings (id),
        created_at timestamptz DEFAULT CURRENT_TIMESTAMP,
        updated_at timestamptz DEFAULT CURRENT_TIMESTAMP
    );

-- TYPOLOGIES
CREATE TABLE
    typologies (
        id uuid PRIMARY KEY DEFAULT uuid_generate_v4 (),
        name varchar NOT NULL,
        description text,
        created_at timestamptz DEFAULT CURRENT_TIMESTAMP,
        updated_at timestamptz DEFAULT CURRENT_TIMESTAMP
    );

-- DOCUMENTS
CREATE TABLE
    documents (
        id uuid PRIMARY KEY DEFAULT uuid_generate_v4 (),
        zoning_id uuid REFERENCES zonings (id),
        zone_id uuid REFERENCES zones (id),
        typology_id uuid REFERENCES typologies (id),
        content_json jsonb,
        html_content text,
        pdf_storage_path text,
        source_plu_url varchar,
        source_plu_date varchar,
        created_at timestamptz DEFAULT CURRENT_TIMESTAMP,
        updated_at timestamptz DEFAULT CURRENT_TIMESTAMP
    );