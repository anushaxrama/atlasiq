# API examples

The running local API is http://127.0.0.1:8020. Its typed OpenAPI documentation is `/docs`, with schema JSON at `/openapi.json`. No public deployment URL is assigned.

```sh
curl 'http://127.0.0.1:8020/health'
curl 'http://127.0.0.1:8020/ready'
curl 'http://127.0.0.1:8020/api/summary?start=2025-01-01&end=2025-01-31'
curl 'http://127.0.0.1:8020/api/trends?start=2025-01-01&end=2025-01-31&zone=161'
curl 'http://127.0.0.1:8020/api/zones?limit=10&offset=0'
curl 'http://127.0.0.1:8020/api/weather?start=2025-01-01&end=2025-01-31'
curl 'http://127.0.0.1:8020/api/anomalies?limit=10'
curl 'http://127.0.0.1:8020/api/quality?limit=20&offset=0'
curl 'http://127.0.0.1:8020/api/runs?limit=20&offset=0'
```

Responses preserve explicit units (`fare_usd`, `distance_miles`, `duration_minutes`, `temp_c`, `precipitation_mm`). Null weather and unknown aggregate values remain null. The selected accepted sample has 95,783 observed trips; no extrapolation is applied. Invalid dates, zones, excessive pagination and reversed/oversized ranges return 422. Unpublished/unavailable analytical data returns 503 with a helpful message; operational run/quality endpoints remain available when the database can be queried.
