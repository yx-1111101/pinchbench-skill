# API Endpoint Extraction and Call Process

## Endpoint found in `config.json`
- URL: `https://api.example.com/v2/data`
- Method: `GET`
- Headers:
  - `Content-Type: application/json`
  - `Accept: application/json`
- Timeout: `30` seconds

## What was created
- `call_api.py`: a Python script that:
  1. Reads `config.json`
  2. Extracts the API endpoint settings
  3. Sends the configured HTTP request
  4. Prints the response status and body
  5. Handles HTTP and connection errors cleanly

## How to run it
From this directory, run:

```bash
python3 call_api.py
```

## Notes
- The script uses Python's standard library only, so no extra packages are required.
- It assumes `config.json` stays in the same directory as `call_api.py`.
- The configured endpoint appears to be a placeholder example domain, so the request may fail unless the endpoint is replaced with a real API.
