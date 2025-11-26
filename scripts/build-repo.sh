#! /bin/bash

set -e

ID="example-repo"
URL_ROOT="${URL_ROOT:-https://example.com}"
NAME="Example repo"
DESCRIPTION="This is an example repo demonstrating automatic builds to github pages"

mkdir -p dist/models
mkdir -p dist/profiles
mkdir -p dist/slices

echo "Copying raw repo files"
cp -r data/json/* dist/

for model_file in data/models/*.spec.json; \
    do python converter/gorc_im_converter.py --config "$model_file"; \
done

python converter/create_repo.py \
    --source_dir dist \
    --url_root "$URL_ROOT" \
    --id "$ID" \
    --name "$NAME" \
    --description "$DESCRIPTION"

python converter/update_icons.py \
    "$URL_ROOT" \
    dist/models/*.json dist/profiles/*.json