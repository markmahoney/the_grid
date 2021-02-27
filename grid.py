"""
Turn a The Grid spreadsheet from Google Sheets into a tsv that DIM understands.

Dumps a The Grid from Google Sheets and tries to match weapon and perk rolls
to values from the D2 API. Once it matches the weapons and perks to the API,
it dumps out a list of dimwishlist rows as a TSV that can be imported into
DIM.
"""

import os
import sys
import csv
import json
import tempfile
import requests

from typing import Dict, Tuple, Set, List
from urllib.parse import urljoin


def _normalize_name(name: str) -> str:
    return " ".join(
        "".join(c for c in token if c.isalnum()) for token in name.lower().split()
    )


def _fetch_grid(sheet_id: str) -> List[Tuple[str, str, str]]:
    csv_url = f"https://docs.google.com/spreadsheets/d/{sheet_id}/gviz/tq?tqx=out:csv"
    resp = requests.get(csv_url)
    resp.raise_for_status()

    reader = csv.DictReader(
        line.decode(resp.apparent_encoding) for line in resp.iter_lines()
    )

    return [
        tuple(_normalize_name(row[col]) for col in ["Name", "Perk 1", "Perk 2"])
        for row in reader
    ]


def _fetch_json(url: str, api_key: str = "") -> Dict:
    resp = requests.get(url, headers={"X-API-Key": api_key})
    resp.raise_for_status()
    return resp.json()


def _fetch_manifest(api_key: str = "") -> Dict:
    resp = _fetch_json("https://www.bungie.net/platform/Destiny2/Manifest/", api_key)

    if resp["ErrorStatus"] != "Success":
        raise ValueError(f"Bungie API error: {resp['Message']}")

    return resp["Response"]


def _fetch_content(manifest: Dict, key: str, api_key: str = "") -> Dict:
    content_url_path = manifest["jsonWorldComponentContentPaths"]["en"][key]
    content_url = urljoin("https://bungie.net", content_url_path)
    data = _fetch_json(content_url, api_key)

    return data


def _weapon_names_and_hashes(categories: Dict, items: Dict) -> Dict[int, str]:
    """Return a mapping of item hash to name that only contains weapons."""
    weapon_hash = next(
        c["hash"]
        for c in categories.values()
        if c["displayProperties"]["name"] == "Weapon"
    )

    return {
        _normalize_name(v["displayProperties"]["name"]): k
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
) -> Dict[str, int]:
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
        _normalize_name(items[perk_id]["displayProperties"]["name"]): perk_id
        for perk_id in perk_ids
    }


def _wishlist_url(weapon_hash: int, perk_hashes: List[int], comment: str) -> str:
    perks = ",".join(str(p) for p in perk_hashes)
    return f"dimwishlist:item={weapon_hash}&perks={perks}#notes: {comment}"


def main():
    grid_key = "1fPE6BTWjTZlfNOGp6kPOrT6ZqUMasbgHQzJanyHnz48"
    grid_rolls = _fetch_grid(grid_key)

    # pull a bunch of JSON blobs from the D2 API
    #
    # the manifest is an index into a bunch of different content blobs
    # that we can pull separately so we don't have to download the entirety
    # of game data for Destiny 2.
    #
    # once we have the manifest we can pull categories and items to get a list
    # of all weapons and their API hashes.
    manifest = _fetch_manifest()

    items = _fetch_content(manifest, "DestinyInventoryItemDefinition")
    categories = _fetch_content(manifest, "DestinyItemCategoryDefinition")
    plug_sets = _fetch_content(manifest, "DestinyPlugSetDefinition")

    weapons_by_name = _weapon_names_and_hashes(categories, items)
    perks_by_name = _all_random_roll_perks(categories, items, plug_sets)

    with open("./the_grid.tsv", "w") as f:
        print("title:the grid", file=f)
        print("description: it's the grid baby", file=f)
        for weapon, p1, p2 in grid_rolls:
            item_hash = weapons_by_name.get(weapon)

            if not item_hash:
                print(f"warning: skipping weapon: missing weapon: {weapon}")
                continue

            p1_hash = perks_by_name.get(p1)
            if not p1_hash:
                print(f"warning: skipping weapon: missing perk: {p1}")
                continue

            p2_hash = perks_by_name.get(p2)
            if not p2_hash:
                print(f"warning: skipping weapon: missing perk: {p2}")
                continue

            print(
                _wishlist_url(
                    item_hash,
                    [p1_hash, p2_hash],
                    f"the grid (season 13) - {weapon}, {p1}, {p2}",
                ),
                file=f,
            )


if __name__ == "__main__":
    main()
