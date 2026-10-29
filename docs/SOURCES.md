# Source discovery

Verified official documentation:
- TLC records: https://www.nyc.gov/site/tlc/about/tlc-trip-record-data.page
- Yellow data dictionary: https://www.nyc.gov/assets/tlc/downloads/pdf/data_dictionary_trip_records_yellow.pdf
- NYC terms: https://www.nyc.gov/main/terms-of-use
- AWS registry: https://registry.opendata.aws/nyc-tlc-trip-records-pds/
- NOAA Global Summary of the Day: https://www.ncei.noaa.gov/data/global-summary-of-the-day/access/2025/72503014732.csv
- Federal holiday reference: https://www.opm.gov/policy-data-oversight/pay-leave/federal-holidays/

TLC publishes monthly, typically with a two-month lag, and does not guarantee source accuracy. The 2025 Yellow schema includes cbd_congestion_fee. Taxi activity is not total mobility or economic activity; fare amounts are observed charges, not profit or corporate revenue. Retain source URLs, retrieval timestamps and file checksums with every load. Do not assign a blanket Creative Commons license to NYC records; retain official attribution and source terms.

NOAA daily station observations are selected instead of Open-Meteo reanalysis to keep the weather source observational and freely reproducible. NOAA US-government data attribution and source-specific metadata must be retained. City-level LaGuardia weather is a proxy applied once per local pickup date, not neighborhood-specific weather. Fahrenheit/inches must be converted to Celsius/millimeters, with sentinel missing values preserved as null. Join weather at a unique date grain to prevent fanout.

Federal holiday labels describe US federal observed dates, not every NYC school, religious, local or business closure. Calendar implementation uses pinned python-holidays rules and is checked against the OPM schedule.
