import sys
import json
import glob
import os
import argparse


def parse_repo_obj(json_path: str, include_model_id=False):
    repo_obj = {
        "ref": json_path,
    }
    if include_model_id:
        with open(json_path, "r") as f:
            data = json.load(f)
            try:
                repo_obj["modelId"] = data["modelId"]
            except KeyError:
                raise ValueError(f"Missing modelId in file: {json_path}")
    return repo_obj


def update_ref(data: dict, source_dir: str, url_root: str):
    return {
        **data,
        "ref": data["ref"].replace(source_dir, url_root)
    }


def repo_from_dir(source_dir: str, url_root: str, id: str, name: str, description: str):
    models_glob = os.path.join(source_dir, "models/*.json")
    profiles_glob = os.path.join(source_dir, "profiles/*.json")
    slices_glob = os.path.join(source_dir, "slices/*.json")

    repo = {
        "url": f"{url_root}/root.json",
        "id": id,
        "name": name,
        "description": description,
        "baseModels": [
            update_ref(parse_repo_obj(path), source_dir, url_root)
            for path in glob.glob(models_glob)
        ],
        "profiles": [
            update_ref(parse_repo_obj(path, include_model_id=True), source_dir, url_root)
            for path in glob.glob(profiles_glob)
        ],
        "thematicSlices": [
            update_ref(parse_repo_obj(path, include_model_id=True), source_dir, url_root)
            for path in glob.glob(slices_glob)
        ],
    }
    return repo


def main(argv):
    parser = argparse.ArgumentParser(
        prog="repo-builder",
        description="This script creates a repo root from a number of json sources"
    )
    parser.add_argument("--source_dir", type=str, required=True)
    parser.add_argument("--url_root", type=str, required=True)
    parser.add_argument("--id", type=str, required=True)
    parser.add_argument("--name", type=str, required=True)
    parser.add_argument("--description", type=str, required=True)


    args = parser.parse_args(argv)
    repo = repo_from_dir(
        source_dir=args.source_dir,
        url_root=args.url_root,
        id=args.id,
        name=args.name,
        description=args.description
    )
    repo_path = os.path.join(args.source_dir, "root.json")
    print(f"Writing repo to {repo_path}")
    with open(repo_path, "w") as f:
        f.write(json.dumps(repo, indent=2))


if __name__ == "__main__":
    main(sys.argv[1:])