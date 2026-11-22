# encoding = utf-8
import json
import re

LINK_RE = re.compile(
    r'(https?://[^"\'\s<>]+/(ServiceTags_Public_(\d{8})\.json))'
)
HEADERS = {"User-Agent": "TA-azure-public-service-tag-and-ip-download"}


def validate_input(helper, definition):
    pass


def find_download_link(page_text):
    """Return (url, file_name, yyyymmdd) from the Microsoft download page, or None."""
    m = LINK_RE.search(page_text)
    if not m:
        return None
    return m.group(1), m.group(2), int(m.group(3))


def collect_events(helper, ew):
    url = helper.get_arg("download_url")
    index = helper.get_arg("index")
    input_name = helper.get_input_stanza_names()
    sourcetype = helper.get_sourcetype()
    source = "azure://{}".format(input_name)
    checkpoint_key = "{}_latest_date".format(input_name)

    try:
        page = helper.send_http_request(url, "GET", headers=HEADERS, timeout=120)
        page.raise_for_status()
    except Exception as e:
        helper.log_error("Failed to fetch download page {}: {}".format(url, e))
        return

    found = find_download_link(page.text)
    if not found:
        helper.log_error("No ServiceTags_Public_<date>.json link found on {}".format(url))
        return
    deep_link, file_name, latest_date = found
    helper.log_info("Found {} at {}".format(file_name, deep_link))

    if helper.get_arg("checkpointing"):
        checkpoint = int(helper.get_check_point(checkpoint_key) or 0)
        helper.log_info("Checkpoint {}={}".format(checkpoint_key, checkpoint))
        if latest_date <= checkpoint:
            helper.log_info("Ignoring download of already indexed file {}".format(file_name))
            return

    try:
        resp = helper.send_http_request(deep_link, "GET", headers=HEADERS, timeout=200)
        resp.raise_for_status()
        items = resp.json().get("values", [])
    except Exception as e:
        helper.log_error("Failed to download/parse {}: {}".format(deep_link, e))
        return

    for item in items:
        ew.write_event(helper.new_event(
            json.dumps(item), index=index, source=source,
            sourcetype=sourcetype, done=True, unbroken=True))

    helper.log_info("Indexed {} events from {} into index={} sourcetype={}".format(
        len(items), file_name, index, sourcetype))

    if helper.get_arg("checkpointing"):
        helper.save_check_point(checkpoint_key, latest_date)
        helper.log_info("Set checkpoint {}={}".format(checkpoint_key, latest_date))
