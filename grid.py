"""
Dump lookup tables of all Legendary weapons and perks to CSVs for
importing into Google sheets.

The Destiny 2 API is self-referential madness and undocumented. Spelunking
is best done through https://data.destinysets.com
"""

import os
import sys
import csv
import json
import tempfile
import requests

from typing import Dict, Tuple, Set
from urllib.parse import urljoin


def _fetch_json(url: str, api_key: str) -> Tuple[int, Dict]:
    resp = requests.get(url, headers={"X-API-Key": api_key})

    try:
        body_json = resp.json()
    except ValueError:
        body_json = None

    return resp.status_code, body_json


def _fetch_manifest(api_key: str) -> Dict:
    code, resp = _fetch_json(
        "https://www.bungie.net/platform/Destiny2/Manifest/", api_key
    )

    if code != 200 or resp["ErrorStatus"] != "Success":
        raise ValueError(f"error fetching manifest: {resp['Message']}")

    return resp["Response"]


def _fetch_content(manifest: Dict, key: str, api_key: str = "") -> Dict:
    content_url_path = manifest["jsonWorldComponentContentPaths"]["en"][key]
    content_url = urljoin("https://bungie.net", content_url_path)
    code, data = _fetch_json(content_url, api_key)

    if code != 200:
        raise ValueError(f"error fetching content blob: {resp.status_code}")

    return data


def _weapon_names_and_hashes(categories: Dict, items: Dict) -> Dict[int, str]:
    """Return a mapping of item hash to name that only contains weapons."""
    weapon_hash = next(
        c["hash"]
        for c in categories.values()
        if c["displayProperties"]["name"] == "Weapon"
    )

    return {
        k: v["displayProperties"]["name"]
        for (k, v) in items.items()
        if weapon_hash in v.get("itemCategoryHashes", [])
    }


def _random_roll_perk_ids(item_id: int, items: Dict, plug_sets: Dict) -> Set[int]:
    perk_hashes = set()

    for socket_entry in items[str(item_id)].get("sockets", {}).get("socketEntries", []):
        # filter by whether or not there's a random roll of this socket.
        #
        # maybe also filter by socket type? this seems ok for now.
        if "randomizedPlugSetHash" in socket_entry:
            plug_set_hash = str(socket_entry["randomizedPlugSetHash"])
            plug_set_item_hashes = [
                str(plug["plugItemHash"])
                for plug in plug_sets[plug_set_hash]["reusablePlugItems"]
            ]
            perk_hashes = perk_hashes.union(set(plug_set_item_hashes))

    return perk_hashes


def _all_random_roll_perks(
    categories: Dict, items: Dict, plug_sets: Dict
) -> Dict[int, str]:
    """
    Dump a map from perk hash to perk name by collecting all possible rolls
    on legendary items.
    """
    weapon_hash = next(
        c["hash"]
        for c in categories.values()
        if c["displayProperties"]["name"] == "Weapon"
    )

    perk_ids = set()

    for item in items.values():
        if not weapon_hash in item.get("itemCategoryHashes", []):
            continue

        perk_ids = perk_ids.union(_random_roll_perk_ids(item["hash"], items, plug_sets))

    return {
        perk_id: items[perk_id]["displayProperties"]["name"] for perk_id in perk_ids
    }


def main():
    api_key = os.getenv("BUNGIE_API_KEY")
    if not api_key:
        print("error: can't find bungie api key")
        sys.exit(-1)

    # pull a bunch of JSON blobs from the D2 API
    #
    # the manifest is an index into a bunch of different content blobs
    # that we can pull separately so we don't have to download the entirety
    # of game data for Destiny 2.
    #
    # once we have the manifest we can pull categories and items to get a list
    # of all weapons and their API hashes.
    manifest = _fetch_manifest(api_key)

    items = _fetch_content(manifest, "DestinyInventoryItemDefinition")
    categories = _fetch_content(manifest, "DestinyItemCategoryDefinition")
    plug_sets = _fetch_content(manifest, "DestinyPlugSetDefinition")

    weapon_names = sorted(
        _weapon_names_and_hashes(categories, items).items(), key=lambda x: x[1]
    )
    with open("weapon_names.csv", "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["name", "hash"])

        for h, n in weapon_names:
            writer.writerow([n, h])

    perk_names = sorted(
        _all_random_roll_perks(categories, items, plug_sets).items(), key=lambda x: x[1]
    )
    with open("perk_names.csv", "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["name", "hash"])

        for h, n in perk_names:
            writer.writerow([n, h])


if __name__ == "__main__":
    main()
