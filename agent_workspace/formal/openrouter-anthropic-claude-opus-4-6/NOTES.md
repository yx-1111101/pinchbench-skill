# API Endpoint Extraction and Test Script

## Extracted API endpoint

From `config.json`:

- Endpoint: `https://api.example.com/v2/data`
- Method: `GET`
- Timeout: `30` seconds

## Process

1. Read `config.json`.
2. Located the API settings under the `api` object.
3. Extracted the endpoint from `api.endpoint`.
4. Created `call_api.py` to:
   - load `config.json`
   - read the endpoint, method, headers, and timeout
   - send the request using Python's standard library
   - print the HTTP status and response body
   - report HTTP and network errors clearly

## Run

```bash
python3 call_api.py
```

## Files created

- `call_api.py`
- `NOTES.md`
