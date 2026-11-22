[public_ip_tags://<name>]
download_url = <string>
* Microsoft download page that links to ServiceTags_Public_<YYYYMMDD>.json.
* Default: https://www.microsoft.com/en-us/download/details.aspx?id=56519

checkpointing = <bool>
* When true, a file is only indexed if its date is newer than the last one this input indexed.
* Leave enabled unless you want the full file re-indexed on every run.
* Default: true
