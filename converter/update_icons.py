import json
import sys


def read_json(path: str):
    with open(path, "r") as f:
        return json.load(f)


def update_icons_in_file(path: str, url_root: str):
    data = read_json(path)
    updated_data = {
        **data,
        "nodes": [
            {
                **node,
                **({
                    "icon": (
                        node["icon"]
                        if node["icon"].startswith("http")
                        else f"{url_root}{node['icon']}"
                    )
                } if "icon" in node else {})
            }
            for node in data["nodes"]
        ]
    }
    with open(path, "w") as f:
        f.write(json.dumps(updated_data, indent=2))


def update_icons_in_files(paths: list, url_root: str):
    print("Updating icons in files:", paths, url_root)
    for path in paths:
        update_icons_in_file(path, url_root)


if __name__ == "__main__":
    update_icons_in_files(sys.argv[2:], sys.argv[1])