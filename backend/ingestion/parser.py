import csv
import json
import xml.etree.ElementTree as ET
import os
from typing import Iterator, Dict, Any

def detect_format(filepath: str) -> str:
    """
    Detect format based on extension, fallback to simple content inspection.
    """
    ext = os.path.splitext(filepath)[1].lower()
    if ext == '.csv':
        return 'csv'
    elif ext == '.json' or ext == '.jsonl':
        return 'json'
    elif ext == '.xml':
        return 'xml'
    
    # Fallback to content sniffing
    with open(filepath, 'r', encoding='utf-8') as f:
        first_char = f.read(1)
        if first_char == '{' or first_char == '[':
            return 'json'
        elif first_char == '<':
            return 'xml'
    return 'csv'

def _parse_csv_array(value: str) -> list:
    """Helper to parse semicolon-separated arrays in CSV."""
    if not value:
        return []
    return [v.strip() for v in value.split(';')]

def _cast_amount(value: Any) -> Any:
    """Convert amount strings to appropriate types if needed before validation."""
    if isinstance(value, list):
        return [_cast_single_amount(v) for v in value]
    return _cast_single_amount(value)

def _cast_single_amount(value: Any) -> Any:
    if value is None or value == '':
        return None
    return value

def parse_csv(filepath: str) -> Iterator[Dict[str, Any]]:
    with open(filepath, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            # Handle array fields which are semicolon delimited in CSV
            for array_field in ['input_addresses', 'output_addresses', 'input_amounts', 'output_amounts']:
                if array_field in row:
                    row[array_field] = _parse_csv_array(row[array_field])
            yield row

def parse_json(filepath: str) -> Iterator[Dict[str, Any]]:
    with open(filepath, 'r', encoding='utf-8') as f:
        # Check if it's JSONL or a single JSON array
        first_char = f.read(1)
        f.seek(0)
        if first_char == '[':
            # JSON array
            data = json.load(f)
            for item in data:
                yield item
        else:
            # Assume JSON Lines
            for line in f:
                line = line.strip()
                if line:
                    yield json.loads(line)

def parse_xml(filepath: str) -> Iterator[Dict[str, Any]]:
    tree = ET.parse(filepath)
    root = tree.getroot()
    for record in root.findall('record'):
        row = {}
        for child in record:
            # If the child has children, it's an array
            if len(child) > 0:
                row[child.tag] = [item.text for item in child]
            else:
                row[child.tag] = child.text
        yield row

def parse_file(filepath: str) -> Iterator[Dict[str, Any]]:
    fmt = detect_format(filepath)
    if fmt == 'csv':
        yield from parse_csv(filepath)
    elif fmt == 'json':
        yield from parse_json(filepath)
    elif fmt == 'xml':
        yield from parse_xml(filepath)
    else:
        raise ValueError(f"Unsupported file format for {filepath}")
