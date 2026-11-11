import argparse
import json
import math
import xml.etree.ElementTree as ET
from pathlib import Path


def parse_value(value):
    value = value.strip()
    try:
        return int(value)
    except ValueError:
        try:
            number = float(value)
        except ValueError:
            return value
        if not math.isfinite(number):
            raise ValueError(f"non-finite numeric value: {value}")
        return number


def parse_node(node):
    children = {child.tag: child for child in node}
    if {"rows", "cols", "dt", "data"}.issubset(children):
        rows_text = children["rows"].text
        cols_text = children["cols"].text
        type_text = children["dt"].text
        data_text = children["data"].text
        if None in (rows_text, cols_text, type_text, data_text):
            raise ValueError(f"matrix <{node.tag}> is missing a value")
        rows = int(rows_text)
        cols = int(cols_text)
        if rows < 0 or cols < 0:
            raise ValueError(f"matrix <{node.tag}> has negative dimensions")
        values = [parse_value(item) for item in data_text.split()]
        if any(not isinstance(value, (int, float)) for value in values):
            raise ValueError(f"matrix <{node.tag}> contains non-numeric data")
        if len(values) != rows * cols:
            raise ValueError(
                f"matrix <{node.tag}> declares {rows}x{cols} entries "
                f"but contains {len(values)} values"
            )
        return {
            "rows": rows,
            "cols": cols,
            "dt": type_text.strip(),
            "data": values,
        }

    if children:
        return {child.tag: parse_node(child) for child in node}
    return parse_value(node.text or "")


def convert_xml(input_path):
    root = ET.parse(input_path).getroot()
    return {child.tag: parse_node(child) for child in root}


def main():
    parser = argparse.ArgumentParser(
        description="Convert an OpenCV FileStorage XML file to JSON."
    )
    parser.add_argument("input", type=Path, help="input XML file")
    parser.add_argument(
        "output",
        nargs="?",
        type=Path,
        help="output JSON file (defaults to the input name with a .json extension)",
    )
    args = parser.parse_args()
    output_path = args.output or args.input.with_suffix(".json")

    try:
        result = convert_xml(args.input)
        output_path.write_text(
            json.dumps(result, indent=2) + "\n",
            encoding="utf-8",
        )
    except (OSError, ET.ParseError, ValueError) as error:
        parser.error(str(error))

    print(f"Saved JSON to {output_path}")


if __name__ == "__main__":
    main()
