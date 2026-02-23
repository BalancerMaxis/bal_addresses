#!/usr/bin/env python3
"""
Validate that all Ethereum addresses in JSON files are checksummed (EIP-55).
Exits with code 1 if any address is not checksummed or invalid.

Usage:
    python validate_checksums.py              # Validate extras/*.json
    python validate_checksums.py --fix        # Fix addresses in-place
    python validate_checksums.py file.json    # Validate specific file(s)
"""

import argparse
import json
import re
import sys
from pathlib import Path

from eth_utils import is_checksum_address, to_checksum_address, is_hex_address

ETH_ADDRESS_PATTERN = re.compile(r"^0x[a-fA-F0-9]{40}$")


def _checksum_str(s):
    """Checksum a string if it's an Ethereum address, otherwise return as-is."""
    if ETH_ADDRESS_PATTERN.match(s) and is_hex_address(s):
        return to_checksum_address(s)
    return s


def checksum_addresses_in_obj(obj):
    """Recursively checksum all Ethereum addresses in a JSON object (keys and values)."""
    if isinstance(obj, dict):
        return {_checksum_str(k): checksum_addresses_in_obj(v) for k, v in obj.items()}
    elif isinstance(obj, list):
        return [checksum_addresses_in_obj(item) for item in obj]
    elif isinstance(obj, str):
        return _checksum_str(obj)
    else:
        return obj


def find_addresses_in_obj(obj, path=""):
    """Recursively find all Ethereum addresses in a JSON object (keys and values)."""
    addresses = []

    if isinstance(obj, dict):
        for key, value in obj.items():
            new_path = f"{path}.{key}" if path else key
            if ETH_ADDRESS_PATTERN.match(key):
                addresses.append((f"{path}[key]" if path else "[key]", key))
            addresses.extend(find_addresses_in_obj(value, new_path))
    elif isinstance(obj, list):
        for i, item in enumerate(obj):
            addresses.extend(find_addresses_in_obj(item, f"{path}[{i}]"))
    elif isinstance(obj, str):
        if ETH_ADDRESS_PATTERN.match(obj):
            addresses.append((path, obj))

    return addresses


def validate_json_file(filepath: Path) -> list[tuple[str, str, str]]:
    """
    Validate all addresses in a JSON file.
    Returns list of (path, address, issue) tuples for invalid/non-checksummed addresses.
    """
    issues = []

    try:
        with open(filepath) as f:
            data = json.load(f)
    except json.JSONDecodeError as e:
        return [("", "", f"Invalid JSON: {e}")]

    addresses = find_addresses_in_obj(data)

    for json_path, address in addresses:
        # Skip zero address
        if address == "0x0000000000000000000000000000000000000000":
            continue

        if not is_hex_address(address):
            issues.append((json_path, address, "Invalid hex address"))
            continue

        if not is_checksum_address(address):
            try:
                checksummed = to_checksum_address(address)
                issues.append((json_path, address, f"Should be: {checksummed}"))
            except Exception as e:
                issues.append((json_path, address, f"Cannot checksum: {e}"))

    return issues


def fix_json_file(filepath: Path) -> tuple[int, list[tuple[str, str]]]:
    """
    Fix all addresses in a JSON file.
    Returns (count of fixed addresses, list of invalid addresses that couldn't be fixed).
    """
    with open(filepath) as f:
        data = json.load(f)

    # Find all addresses and check for invalid ones
    addresses = find_addresses_in_obj(data)
    invalid = []
    non_checksummed = 0

    for json_path, addr in addresses:
        if addr == "0x0000000000000000000000000000000000000000":
            continue
        if not is_hex_address(addr):
            invalid.append((json_path, addr))
        elif not is_checksum_address(addr):
            non_checksummed += 1

    if non_checksummed == 0:
        return 0, invalid

    # Fix valid addresses (invalid ones pass through unchanged)
    fixed_data = checksum_addresses_in_obj(data)

    # Write back with consistent formatting
    with open(filepath, "w") as f:
        json.dump(fixed_data, f, indent=2)
        f.write("\n")

    return non_checksummed, invalid


def main():
    parser = argparse.ArgumentParser(
        description="Validate or fix Ethereum address checksums in JSON files"
    )
    parser.add_argument(
        "--fix",
        action="store_true",
        help="Fix addresses in-place instead of validating",
    )
    parser.add_argument(
        "files", nargs="*", help="JSON files to process (default: extras/*.json)"
    )
    args = parser.parse_args()

    # Collect JSON files
    json_files = []
    if args.files:
        json_files = [Path(f) for f in args.files if f.endswith(".json")]
    else:
        for dir_name in ["config", "extras"]:
            dir_path = Path(dir_name)
            if dir_path.exists():
                json_files.extend(dir_path.glob("*.json"))

    if not json_files:
        print("No JSON files to process")
        sys.exit(0)

    if args.fix:
        # Fix mode
        total_fixed = 0
        all_invalid = []

        for filepath in sorted(json_files):
            fixed, invalid = fix_json_file(filepath)
            if fixed > 0:
                print(f"Fixed {fixed} address(es) in {filepath}")
                total_fixed += fixed
            if invalid:
                all_invalid.append((filepath, invalid))

        if all_invalid:
            print("\nInvalid addresses that cannot be checksummed:")
            for filepath, invalid in all_invalid:
                print(f"  {filepath}:")
                for json_path, addr in invalid:
                    print(f"    {json_path}: {addr}")
            sys.exit(1)

        if total_fixed > 0:
            print(f"\nTotal: {total_fixed} address(es) fixed")
        else:
            print("All addresses were already checksummed")
        sys.exit(0)
    else:
        # Validate mode
        all_issues = []

        for filepath in sorted(json_files):
            issues = validate_json_file(filepath)
            if issues:
                all_issues.append((filepath, issues))

        if all_issues:
            print("Address checksum validation failed!\n")
            for filepath, issues in all_issues:
                print(f"{filepath}:")
                for json_path, address, issue in issues:
                    print(f"   {json_path}: {address}")
                    print(f"      -> {issue}")
                print()

            total = sum(len(issues) for _, issues in all_issues)
            print(f"Total: {total} address(es) need fixing")
            print("\nRun with --fix to auto-correct")
            sys.exit(1)
        else:
            print(
                f"All {len(json_files)} JSON files have properly checksummed addresses"
            )
            sys.exit(0)


if __name__ == "__main__":
    main()
