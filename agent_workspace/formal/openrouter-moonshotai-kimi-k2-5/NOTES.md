# API endpoint extraction and Python caller

## Extracted API endpoint

- Endpoint: `https://api.example.com/v2/data`
- Method: `GET`
- Timeout: `30` seconds

## Source

The endpoint was read from `config.json` under:

- `api.endpoint`

## Python script

Created `call_api.py`, which:

1. Loads `config.json`
2. Reads `api.endpoint`, `api.method`, `api.headers`, and `api.timeout`
3. Sends the HTTP request using Python's standard library
4. Prints the response status and body

## How to run

```bash
python3 call_api.py
```

## Notes

- The script uses `urllib.request`, so it does not require third-party packages.
- If `config.json` changes, the script will automatically use the updated endpoint and request settings.
