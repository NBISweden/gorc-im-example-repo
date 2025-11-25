import openpyxl
import sys
import json
import re
import itertools
import datetime
import argparse
import os


class GORCParser:
    def __init__(
        self,
        columns=None,
        metric_columns=None,
        sheets=None,
        node_extensions=None
    ):
        self.columns = columns
        self.metric_columns = metric_columns
        self.sheets = (
            {
                "\s*introduction\s*": None,
                "\s*glossary\s*": None,
                "\s*kpis & metrics\s*": "metric",
                ".+": "node",
            }
            if sheets is None
            else sheets
        )
        self.node_extensions = node_extensions

    def clean_name(self, name):
        return name.strip().lower()

    def get_sheet_type(self, sheet_name):
        for expression, sheet_type in self.sheets.items():
            if re.match(expression, sheet_name, re.IGNORECASE):
                return sheet_type
        return None

    def parse(
        self,
        excel_file,
        version="0.0.1",
        id="gorc-im-base",
        label="GORC Base Model",
    ):
        """
        Analyzes the Excel workbook, extracts data, and generates a .ts file
        suitable for translation to example-models.ts.
        """

        workbook = openpyxl.load_workbook(excel_file, read_only=True, data_only=True)

        graph_data = {}
        all_nodes = list(self.nodes_from_workbook(workbook))
        nodes = self.extend_nodes(all_nodes, self.node_extensions)
        base_model_package = {
            "version": version,
            "id": id,
            "label": label,
            "updatedAt": datetime.datetime.now().isoformat(),
            "nodes": nodes
        }
        return base_model_package


    def get_keys_of_importance(self, entry):
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


    def get_node_type(self, entry):
        return next(self.get_keys_of_importance(entry))


    def id_from_label(self, label):
        id = label.lower().strip()
        id = re.sub(r"[^\w\s-]", "", id)
        id = re.sub(r"[\s_-]+", "-", id)
        id = re.sub(r"^-+|-+$", "", id)
        return id


    def get_parent_node_id(self, entry):
        try:
            parent_node_type = next(itertools.islice(self.get_keys_of_importance(entry), 1, None))
            return self.id_from_label(entry[parent_node_type])
        except StopIteration:
            return None


    def node_from_entry(self, entry):
        node_type = self.get_node_type(entry)
        name = entry[node_type]
        child_of = self.get_parent_node_id(entry)
        return {
            "id": self.id_from_label(name),
            "type": node_type.replace("_", "-"),
            "name": name,
            "shortName": name,
            **({} if child_of is None else {"childOf": child_of}),
            "considerationLevel":entry.get("consideration_level", "core").lower(),
            "description": entry.get("description", ""),
            "shortDescription": entry.get("description", "")
        }

    def tree_from_entries(self, entries):
        """
        Should return a flat tree structure usable in the GORC IM tool
        """
        return [
            self.node_from_entry(entry)
            for entry in entries
        ]

    def nodes_from_workbook(self, workbook):
        for sheet_name in workbook.sheetnames:
            sheet_type = self.get_sheet_type(sheet_name)
            sheet = workbook[sheet_name]
            print(f"Parsing {sheet_name} as {sheet_type}")
            match sheet_type:
                case "node":
                    entries = self.entries_from_sheet(sheet_name, sheet)
                    for entry in self.enrich_entries(entries):
                        yield self.node_from_entry(entry)
                case "metric":
                    entries = self.metric_entries_from_sheet(sheet)
                    for entry in self.enrich_metrics_entries(entries):
                        yield self.node_from_metric_entry(entry)
                case None:
                    pass
                case _:
                    raise ValueError(f"Incorrectly configured sheet type: '{sheet_type}'")

    def enrich_entries(self, entries):
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

    def entries_from_sheet(self, essential_element, sheet):
        yield {
            "essential_element": essential_element,
            "consideration_level": "core",
        }
        for row in sheet.iter_rows(min_row=3):
            cell_values = [
                None
                if cell.value is None
                else str(cell.value).strip()
                for cell in row
            ]
            column_map = self.create_column_map(
                [
                    "category",
                    "subcategory",
                    "attribute",
                    "feature",
                    "description",
                    "examples",
                    "consideration_level",
                    "primary_source"
                ],
                self.columns
            )
            if any((v is not None for v in cell_values)):
                yield {
                    "essential_element": essential_element,
                    **{
                        key: cell_values[index]
                        for key, index in column_map
                        if index is not None and index < len(cell_values) and cell_values[index] is not None
                    }
                }
    
    def enrich_metrics_entries(self, entries):
        current_context = {}
        for entry in entries:
            current_context = (
                {"theme": entry["theme"]}
                if "theme" in entry
                else {
                    **current_context,
                    "type": entry.get("type", current_context.get("type"))
                }
            )
            if "theme" in current_context and "type" in current_context:
                yield {
                    **entry,
                    **current_context
                }


    def metric_entries_from_sheet(self, sheet):
        for row in sheet.iter_rows(min_row=3):
            cell_values = [
                None
                if cell.value is None
                else str(cell.value).strip()
                for cell in row
            ]
            column_map = self.create_column_map(
                [
                    "theme",
                    "type",
                    "name",
                    "description",
                    "consideration_level",
                    "source",
                    "development_stage",
                    "internal_vs_external_information_needed",
                    "measurement_of",
                    "indicator_of",
                    "child_of",
                    "reasoning"
                ],
                self.metric_columns
            )
            if any((v is not None for v in cell_values)):
                yield {
                    key: cell_values[index]
                    for key, index in column_map
                    if index is not None and index < len(cell_values) and cell_values[index] is not None
                }
    
    def node_from_metric_entry(self, entry):
        node_type = {
            "kpis": "kpi",
            "metrics": "metric",
            "kpi": "kpi",
            "metric": "metric",
        }[self.id_from_label(entry["type"])]
        name = entry["name"]
        return {
            "id": self.id_from_label(name),
            "type": node_type,
            "name": name,
            "shortName": name,
            "indicatorOf": self.id_from_label(entry["indicator_of"]),
            "measurementOf": self.id_from_label(entry["measurement_of"]),
            "considerationLevel":entry.get("consideration_level", "core").lower(),
            "description": entry.get("description", ""),
            "shortDescription": entry.get("description", "")
        }

    def create_column_map(self, column_names, column_dict=None):
        return (
            list(zip(column_names, range(len(column_names))))
            if column_dict is None
            else list(column_dict.items())
        )

    def extend_nodes(self, tree_nodes, node_extensions):
        return [
            (
                {**node, **node_extensions[node["id"]]}
                if node["id"] in node_extensions
                else node
            )
            for node in tree_nodes
        ]


def get_root_node(node, node_map):
    if "childOf" in node:
        return get_root_node(
            node_map[node["childOf"]],
            node_map
        )
    else:
        return node


def generate_basic_slices(model):
    nodes = model["nodes"]
    model_id = model["id"]

    node_map = {
        node["id"]: node
        for node in nodes
    }

    slice_map = dict()
    for node in nodes:
        if node["type"] not in {"kpi", "metric"}:
            root = get_root_node(node, node_map)
            slice_nodes, id_set = slice_map.get(root["id"], ([], set()))
            slice_nodes.append(node)
            id_set.add(node["id"])
            slice_map[root["id"]] = (slice_nodes, id_set)

    kpi_nodes = [
        node
        for node in nodes
        if node["type"] in {"kpi", "metric"}
    ]
    
    return [
        {
            "updatedAt": datetime.datetime.now().isoformat(),
            "modelId": model["id"],
            "version": model["version"],
            "id": f"{model['id']}-slice-{root_id}",
            "label": f"{node_map[root_id]['name']} Slice",
            "nodes": [
                {
                    "nodeId": node["id"]
                }
                for node in [
                    *slice_nodes,
                    *[n for n in kpi_nodes if n["measurementOf"] in slice_ids or n["indicatorOf"] in slice_ids]
                ]
            ]
        }
        for root_id, (slice_nodes, slice_ids) in slice_map.items()
    ]


def parse_config(path: str):
    with open(path, "r") as f:
        config = json.load(f)
        config["config_dir"] = os.path.dirname(path)
        return config


def post_process_config(config):
    return {
        **config,
        **format_config_value(config, "output"),
        **format_config_value(config, "path"),
        **format_config_value(config, "label"),
    }


def format_config_value(config, id):
    return (
        {id: config[id].format(**config)}
        if id in config
        else {}
    )


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
    parser.add_argument("--sliceoutput", type=partial_config_parser("sliceoutput"))
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
    
    return validate_config(post_process_config(config))


def main(argv):
    config = parse_arguments(argv)
    print(f"Converting GORC IM using config:")
    print(json.dumps(config, indent=2))
    parser = GORCParser(
        columns=config.get("columns"),
        node_extensions=config.get("extensions", {})
    )
    base_model_package = parser.parse(
        excel_file=config["path"],
        version=config["version"],
        id=config["id"],
        label=config["label"],
    )
    json_file = config["output"]
    with open(json_file, "w") as f:
        print(f"Writing model: {json_file}")
        f.write(json.dumps(base_model_package, indent=2))
    
    slice_output = config.get("sliceoutput")

    if slice_output:
        slices = generate_basic_slices(base_model_package)
        for model_slice in slices:
            slice_file_path = slice_output.format(
                config_dir=config["config_dir"],
                slice_id=model_slice["id"]
            )
            print(f"Writing slice: {slice_file_path}")
            with open(slice_file_path, "w") as f:
                f.write(json.dumps(model_slice, indent=2))


if __name__ == "__main__":
    main(sys.argv[1:])