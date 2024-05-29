# monitoring service

This is the monitor that will try to perform the following actions every hour:
- Get a 'monitoring' user in the server, create the user if it does not exist
- Spawn a server for the user
- Wait for at most 5 minutes for the server to start
- Delete the server

And writes the result into a json file with this structure:

```json
{
  "time": <time in seconds since UNIX epoch>
  "code": "<OK|WARNING|CRITICAL>",
  "msg": "<extra information about the probe>"
}
```

## Environment

The probe expects the following variables in the environment:
- `JUPYTERHUB_API_URL`: URL where the JupyterHub API is found
- `JUPYTERHUB_API_TOKEN`: token to authenticate against the API
- `JUPYTERHUB_USER`: user to use for monitoring
- `STATUS_FILE`: where to store the json with the result of monitoring (default: `status.json`)
- `DEBUG`: when equal to `TRUE` will produce extra logging information
