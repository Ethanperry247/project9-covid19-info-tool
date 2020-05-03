-- Create the table with COVID data.
DROP TABLE IF EXISTS covid_data;
CREATE TABLE covid_data (
    date date, 
    county text, 
    state text, 
    fips int, 
    cases int, 
    deaths int);

-- Bulk load the data.
\COPY covid_data from './us-counties.csv' WITH (format CSV);

-- Create an index to speed things up considering the massive size of the data.
CREATE INDEX ID ON covid_data (date, county, state, fips, cases, deaths); 