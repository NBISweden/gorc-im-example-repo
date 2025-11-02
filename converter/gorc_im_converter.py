import openpyxl
import sys
import json
import re
import itertools
import datetime
import argparse
import os


def is_data_sheet(sheet_name):
    clean_name = sheet_name.strip().lower()
    return clean_name not in {
        "introduction",
        "glossary",
        "kpis & metrics",
    }


def analyze_excel_and_create_json(
    excel_file,
    json_file,
    version="0.0.1",
    id="gorc-im-base",
    label="GORC Base Model"
):
    """
    Analyzes the Excel workbook, extracts data, and generates a .ts file
    suitable for translation to example-models.ts.
    """

    workbook = openpyxl.load_workbook(excel_file, read_only=True, data_only=True)

    graph_data = {}
    all_entries = list(entries_from_workbook(workbook))
    tree_data = tree_from_entries(all_entries)
    base_model_package = {
        "version": version,
        "id": id,
        "label": label,
        "updatedAt": datetime.datetime.now().isoformat(),
        "nodes": tree_data
    }
    with open(json_file, "w") as f:
        f.write(json.dumps(base_model_package, indent=2))


def get_keys_of_importance(entry):
    context_properties = (
        "essential_element",
        "category",
        "subcategory",
        "attribute",
        "feature",
    )
    for property_key in reversed(context_properties):
        if property_key in entry:
            yield property_key


def get_node_type(entry):
    return next(get_keys_of_importance(entry))


def id_from_label(label):
    id = label.lower().strip()
    id = re.sub(r"[^\w\s-]", "", id)
    id = re.sub(r"[\s_-]+", "-", id)
    id = re.sub(r"^-+|-+$", "", id)
    return id


def get_parent_node_id(entry):
    try:
        parent_node_type = next(itertools.islice(get_keys_of_importance(entry), 1, None))
        return id_from_label(entry[parent_node_type])
    except StopIteration:
        return None


def node_from_entry(entry):
    node_type = get_node_type(entry)
    name = entry[node_type]
    parent_id = get_parent_node_id(entry)
    return {
        "id": id_from_label(name),
        "type": node_type.replace("_", "-"),
        "name": name,
        "shortName": name,
        **({} if parent_id is None else {"parentId": parent_id}),
        "considerationLevel":entry.get("consideration_level", "core").lower(),
        "description": entry.get("description", ""),
        "shortDescription": entry.get("description", "")
    }

def tree_from_entries(entries):
    """
    Should return a flat tree structure usable in the GORC IM tool
    """
    return [
        node_from_entry(entry)
        for entry in entries
    ]


def entries_from_workbook(workbook):
    for sheet_name in workbook.sheetnames:
        if is_data_sheet(sheet_name):
            sheet = workbook[sheet_name]
            entries = list(entries_from_sheet(sheet_name, sheet))

            for entry in enrich_entries(entries):
                yield entry


def enrich_entries(entries):
    current_context = {}
    context_properties = (
        "essential_element",
        "category",
        "subcategory",
        "attribute",
        "feature",
    )
    for entry in entries:
        last_key_index = max([
            index
            for index, key in enumerate(context_properties)
            if key in entry
        ])
        entry_context = {
            property_key: entry.get(property_key, current_context.get(property_key))
            for property_key in context_properties[0:last_key_index + 1]
            if property_key in entry or property_key in current_context
        }
        current_context = entry_context
        yield {
            **entry,
            **entry_context
        }


def entries_from_sheet(essential_element, sheet):
    yield {
        "essential_element": essential_element,
        "consideration_level": "core",
    }
    for row in sheet.iter_rows(min_row=3):
        cell_values = [cell.value for cell in row]
        columns = [
            "category",
            "subcategory",
            "attribute",
            "feature",
            "description",
            "examples",
            "consideration_level",
            "primary_source"
        ]
        yield {
            "essential_element": essential_element,
            **{
                key: value
                for key, value in zip(columns, cell_values)
                if value is not None
            }
        }


def parse_config(path: str):
    with open(path, "r") as f:
        data = json.load(f)
        basename = f"{data.get("id", id_from_label(os.path.basename(path)))}.json"
        output = (
            {"output": os.path.join(os.path.dirname(path), data["output_dir"], basename)}
            if "output_dir" in data
            else {}
        )
        path = os.path.join(os.path.dirname(path), data["path"])
        return {
            **data,
            **output,
            "path": path,
        }


def partial_config_parser(id: str, type_func=str):
    def _config_parser(value: str):
        return {
            id: type_func(value)
        }
    return _config_parser


def validate_config(config: dict):
    missing_values = [
        required_value
        for required_value in [
            "output",
            "path",
            "type",
            "version",
            "label",
            "id"
        ] if required_value not in config
    ]
    if len(missing_values) > 0:
        raise ValueError(f"Missing value(s) in config: {', '.join(missing_values)}")
    return config


def parse_arguments(argv):
    parser = argparse.ArgumentParser(
        prog="gorc-im-converter",
        description="This script converts files to json models fit for use with the interactive GORC model viewer."
    )
    parser.add_argument("--config", type=parse_config)
    parser.add_argument("--output", type=partial_config_parser("output"))
    parser.add_argument("--output_dir", type=partial_config_parser("output"))
    parser.add_argument("--path", type=partial_config_parser("path"))
    parser.add_argument("--type", type=partial_config_parser("type"))
    parser.add_argument("--version", type=partial_config_parser("version"))
    parser.add_argument("--label", type=partial_config_parser("label"))
    parser.add_argument("--id", type=partial_config_parser("id"))

    args = vars(parser.parse_args(argv))
    base_config = args["config"]
    config = dict() if base_config is None else base_config
    for key, value in args.items():
        if key != "config" and value is not None:
            config.update(value)
    
    return validate_config(config)


def main(argv):
    config = parse_arguments(argv)
    print(f"Converting GORC IM using config:")
    print(json.dumps(config, indent=2))
    analyze_excel_and_create_json(
        excel_file=config["path"],
        json_file=config["output"],
        version=config["version"],
        id=config["id"],
        label=config["label"]
    )


if __name__ == "__main__":
    main(sys.argv[1:])