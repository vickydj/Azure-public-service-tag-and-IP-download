# Azure public service tag and IP download

A Splunk add-on that downloads Microsoft's **Azure IP Ranges and Service Tags – Public Cloud** file
(<https://www.microsoft.com/en-us/download/details.aspx?id=56519>) and indexes each service tag as a JSON event.

## Requirements
- Splunk Enterprise 10.x or Splunk Cloud (Python 3.13)
- Outbound HTTPS from the Splunk instance running the input to `www.microsoft.com` and `download.microsoft.com`
  (or a proxy, configurable under **Configuration → Proxy**)

## Setup
1. Install the add-on on a heavy forwarder or search head and restart if prompted.
2. Open the add-on, go to **Inputs → Create New Input**.
3. Set a name, an interval (default **86400** seconds — Microsoft publishes a new file weekly) and a target index.
4. Keep **Checkpointing** enabled to index a file only when Microsoft publishes a newer one.

## Data
| Field | Value |
|---|---|
| sourcetype | `azure:assets` |
| source | `azure://<input name>` |
| One event per | service tag (`values[]` entry in the JSON file) |

Each event contains `name`, `id` and `properties` (`changeNumber`, `region`, `platform`, `systemService`,
`addressPrefixes{}`, `networkFeatures{}`). Large tags such as `AzureCloud` exceed 250 KB, so `TRUNCATE = 0` is set.

## Example searches
Latest prefixes per service tag:
```
index=<your index> sourcetype=azure:assets
| stats latest(_raw) as _raw by name
| spath path=properties.addressPrefixes{} output=prefix
| mvexpand prefix
| table name prefix
```

Build a CIDR lookup (add a `transforms.conf` lookup with `match_type = CIDR(prefix)`):
```
... | outputlookup azure_service_tags.csv
```

## Troubleshooting
The input logs to `$SPLUNK_HOME/var/log/splunk/ta_azure_public_service_tag_and_ip_download_public_ip_tags.log`:
```
index=_internal source=*ta_azure_public_service_tag_and_ip_download_public_ip_tags.log*
```

## Support
Open an issue at <https://github.com/vickydj/Azure-public-service-tag-and-IP-download/issues>.
