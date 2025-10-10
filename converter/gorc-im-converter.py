import openpyxl
import sys
import json
import re
import itertools
import datetime


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


if __name__ == "__main__":
    excel_file = (
        sys.argv[1]
        if len(sys.argv) > 1
        else "./GORC_International_Model_WG-CommonsModelV1.1.xlsx"
    )
    json_file = (
        sys.argv[2]
        if len(sys.argv) > 2
        else "gorc-model-output.json"
    )
    print(f"Converting GORC IM Excel to JSON: {excel_file} -> {json_file}")
    analyze_excel_and_create_json(excel_file, json_file)
