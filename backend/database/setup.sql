-- Create the database
CREATE DATABASE scriptys_day_off;

-- Connect to the database
\c scriptys_day_off

-- Create the user with password
CREATE USER scripty WITH PASSWORD 'password';

-- Grant all privileges on the database
GRANT ALL PRIVILEGES ON DATABASE scriptys_day_off TO scripty;

-- Grant privileges on the public schema (required for PostgreSQL 15+)
GRANT ALL ON SCHEMA public TO scripty;
