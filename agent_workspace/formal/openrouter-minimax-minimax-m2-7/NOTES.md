# API endpoint extraction and Python caller

## Extracted endpoint

- Endpoint: `https://api.example.com/v2/data`
- Method: `GET`
- Timeout: `30` seconds

## Source

The endpoint was read from `config.json`:

```json
{
  "api": {
    "endpoint": "https://api.example.com/v2/data",
    "method": "GET",
    "headers": {
      "Content-Type": "application/json",
      "Accept": "application/json"
    },
    "timeout": 30
  }
}
```

## Script created

File: `call_api.py`

What it does:

1. Loads `config.json`
2. Reads `api.endpoint`, `api.method`, `api.headers`, and `api.timeout`
3. Sends the HTTP request using Python's standard library (`urllib.request`)
4. Prints the response body to stdout
5. Prints request metadata and errors to stderr

## How to run

```bash
python3 call_api.py
```

## Notes

- The script uses the standard library, so no extra package install is required.
- The configured endpoint uses the placeholder domain `api.example.com`, so a real network call will likely fail unless the config is replaced with a real API.
- If `config.json` changes, the script will automatically use the new endpoint and request settings on the next run.
