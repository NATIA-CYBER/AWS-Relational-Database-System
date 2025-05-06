CREATE TABLE IF NOT EXISTS aircraft_stats (
    id SERIAL PRIMARY KEY,
    icao VARCHAR(10) UNIQUE NOT NULL,
    total_flights INTEGER NOT NULL,
    avg_altitude FLOAT NOT NULL,
    avg_speed FLOAT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_aircraft_stats_icao ON aircraft_stats(icao);
