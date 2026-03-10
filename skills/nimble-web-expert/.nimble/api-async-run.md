#### Authorizations

Bearer authentication header of the form `Bearer <token>`, where `<token>` is your auth token.

#### Body

Request body model for the /agent/run endpoint

The agent's name to execute

The agent's input parameters, for example query, prodcut\_id, etc. Depands on the agent used.

Example:

```
{  "query": "What happened last night in the NBA?"}
```

Controls if localization sould be enabled (default false). Some agent support localization based on zip\_code or store\_id on the site it self. Relevant only when agent is supporting localization

Storage type for async results. Use s3 for Amazon S3 and gs for Google Cloud Platform.

Repository URL where output will be saved. Format: s3://Your.Bucket.Name/your/object/name/prefix/ - Output will be saved as TASK\_ID.json

Example:

`"s3://Your.Repository.Path/"`

A URL to callback once the data is delivered. The API will send a POST request with task details (without the requested data) when the task completes.

Example:

`"https://your.callback.url/path"`

When set to true, the response saved to storage\_url will be compressed using GZIP format. If false or not set, response will be saved uncompressed.

Custom name for the stored object instead of the default task ID

#### Response