# API Extraction and Call Notes

## API endpoint
- Endpoint: `https://api.example.com/v2/data`
- Method: `GET`
- Timeout: `30` seconds

## Where it came from
Extracted from `config.json`:
- `api.endpoint`
- `api.method`
- `api.headers`
- `api.timeout`

## Python script
Created `call_api.py` to:
1. Read `config.json`
2. Extract the API settings
3. Send the request using Python's built-in `urllib.request`
4. Print the response status, headers, and body

## How to run
From this directory:

```bash
python3 call_api.py
```

## Notes
- The script uses the headers defined in `config.json`.
- No third-party packages are required.
- The configured endpoint is `api.example.com`, which is commonly a placeholder domain. If the request fails in a real environment, the endpoint may need to be replaced with a live API URL.
