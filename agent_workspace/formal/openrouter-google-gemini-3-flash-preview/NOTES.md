# API Notes

## Extracted API endpoint
- Endpoint: `https://api.example.com/v2/data`
- Method: `GET`
- Timeout: `30` seconds

## Source
These values were read from `config.json` under the `api` object.

## Python script
A runnable client was created at `call_api.py`.

## How it works
1. Reads `config.json` from the same directory.
2. Extracts `api.endpoint`, `api.method`, `api.headers`, and `api.timeout`.
3. Sends the HTTP request using Python's standard library (`urllib.request`).
4. Prints the HTTP status and response body.
5. Prints useful error output for HTTP and network failures.

## Run it
```bash
python3 call_api.py
```

## Notes
- The current config points to `https://api.example.com/v2/data`.
- The script uses only the Python standard library, so no extra package install is needed.
- If `config.json` changes, the script will automatically use the updated endpoint and request settings on the next run.
