import logging
import yaml
import requests
from collections import Counter
from datetime import datetime
import azure.functions as func
from pathlib import Path

DATA_FILE = Path(__file__).parent.parent / "data" / "fixable.yaml"

def main(mytimer: func.TimerRequest) -> None:
    logging.info("Fixable dependency scan started")

    with open(DATA_FILE) as f:
        report = yaml.safe_load(f)

    counter = Counter()

    for image in report:
        for pkg in image.get("fixable", []):
            name = list(pkg.keys())[0].lower()
            counter[name] += 1

    for pkg, count in counter.most_common():
        resp = requests.get(f"https://pypi.org/pypi/{pkg}/json", timeout=10)
        if resp.status_code != 200:
            logging.warning(f"Could not fetch PyPI data for {pkg}")
            continue

        data = resp.json()
        latest = data["info"]["version"]
        releases = data["releases"].get(latest, [])
        updated = releases[0]["upload_time_iso_8601"] if releases else "unknown"

        logging.info(
            f"{pkg}: occurrences={count}, "
            f"latest={latest}, last_updated={updated}"
        )

    logging.info("Fixable dependency scan completed")
