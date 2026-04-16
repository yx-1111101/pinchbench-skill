# API Call Notes

## Extracted endpoint
- Endpoint: `https://api.example.com/v2/data`
- Method: `GET`
- Headers:
  - `Content-Type: application/json`
  - `Accept: application/json`
- Timeout: `30` seconds

## Files created
- `call_api.py` - Python script that reads `config.json` and calls the configured API endpoint.

## Process
1. Read `config.json`.
2. Found the API configuration under the `api` key.
3. Extracted the endpoint and related request settings.
4. Created `call_api.py` using Python's standard library (`urllib.request`) so it does not depend on external packages.
5. The script loads `config.json`, builds the request, sends it, then prints the HTTP status and response body.

## Usage
Run:

```bash
python3 call_api.py
```

## Notes
- The script uses the values in `config.json`, so if the endpoint, method, headers, or timeout change there, the script will automatically use the updated settings.
- Error handling is included for HTTP and network errors.
