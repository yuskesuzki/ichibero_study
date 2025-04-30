CREATE TABLE IF NOT EXISTS points_of_map (
    id SERIAL PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    level INT NOT NULL,
    poi_type INT NOT NULL,
    geom GEOMETRY(Point, 4326) NOT NULL,
    description VARCHAR(255) NULL
);

-- Compare this snippet from postgis-init/01-setup.sql:
CREATE INDEX IF NOT EXISTS points_of_map_geom_idx ON points_of_map USING GIST (geom);

INSERT INTO points_of_map (name, level, poi_type, geom, description) VALUES (
    'sample point 1',
    1,
    1,
    ST_GeometryFromText(
        'POINT(135.6366 35.075)',
        4326
    ),
    'Description for Point 1'
);

INSERT INTO points_of_map (name, level, poi_type, geom, description) VALUES (
    'sample point 2',
    1,
    1,
    ST_GeometryFromText(
        'POINT(135.16366 35.1075)',
        4326
    ),
    'Description for Point 2'
);
