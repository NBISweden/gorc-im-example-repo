# GORC IM Repository Builder
This repository aims to be an example of how one can set up and maintain a `model repository` for the [RDA GORC IM Visualization Tool](https://github.com/NBISweden/rda-gorc-im). It does so by enabling the construction of a `model repository` using two different sources, the GORC International Model spread sheet or JSON data.

This repository has been set up to build github pages containing an example `model repository`. By forking this repository and configuring github actions to build pages it should be possible to easily create a public custom `model repository`.

## Getting started
The easiest way to get trying to run this project locally is by using docker and docker compose. While it is not strictly necessary, this introduction will assume that docker and docker compose are available.

The script `./compose-build-repo.sh` will utilize docker compose to run the scripts needed to build a collection of files representing a `model repository`.

The script `build-repo.sh` is run in a container with a python virtual envirnment containing all dependencies. The script expects data resources structured in the following way:

```yaml
data:
  json:
    icons: A collection of icons to be used for node in the repository
    models: A collection of base model json files
    profiles: A collection of model profile json files
    slices: A collection of model slice json files
  models:
    data: Data used by the *.spec.json files
    .: A collection of *.spec.json files which are used to run the script ./converter/gorc_im_converter.py

```

### The script build-repo.sh
The script `build-repo.sh`, in short will do the following:

1. Copy all the data fron `data/json` to `dist`.
2. Build all `base models` from `*.spec.json` files in `data/models` using `converter/gorc_im_converter.py`.
3. Create a `model repository` root file, `root.json`, using `converter/create_repo.py`.
4. Retarget all icon urls, using `converter/update_icons.py`, in order to allow deployment on any site.

### The *.spec.json file
Each `*.spec.json` is a specification of how to parse an excel file into a `base model` and `slices` to be included in a `model repository`.

The file `data/models/gorc-international-model.spec.json` is an example of a `*.spec.json` file. It uses most of the available functionality of the parser script and will result in one `base model` with the `id` "gorc-im-core" and a number of `model slices`. Where the `model slices` are based on the `essential element` nodes and the `consideration levels`.

In this example the properties can be described as follows:

- `type`: Describes which type of that to be parsed (currently the only option is `excel`)
- `path`: Is the path to the source data to be parsed. `{config_dir}` will be replaced with the dirname of the `*.spec.json` file
- `id`: Is the id of the `base model` output
- `label`: Is the label of the `base model` output
- `version`: Is the version of the `base model` output
- `output`: Is the path template for the output `base model` file. `{config_dir}` will be replaced with the dirname of the `*.spec.json` file and `{id}` will be replaced by the `id` from this configuration
- `sliceoutput`: Is the path template for output `slice` files. `{config_dir}` will be replaced with the dirname of the `*.spec.json` file and `{slice_id}` will be replaced by the id of the slice being exported.
- `id_mapping`: Is a mapping of node ids to be used when the dataset contains incorrect or underspecified references
- `extensions`: Maps data to specific nodes. The data will extend or override the content of the nodes with the given id.

```json
{
    "type": "excel",
    "path": "{config_dir}/data/GORC_International_Model_WG-CommonsModelV1.1.xlsx",
    "id": "gorc-im-core",
    "label": "GORC Base Model",
    "version": "0.0.1",
    "output": "{config_dir}/../../dist/models/{id}.json",
    "sliceoutput": "{config_dir}/../../dist/slices/{slice_id}.json",
    "id_mapping": {
        "ict": "ict-infrastructure",
        "governance-management": "governance-leadership"
    },
    "extensions": {
        "governance-leadership": {
            "icon": "{url_root}/icons/gorc/gorc-icon_governance-and-leadership.svg"
        },
        "rules-of-participation-access": {
            "icon": "{url_root}/icons/gorc/gorc-icon_rules-of-participation-access.svg"
        },
        "sustainability": {
            "icon": "{url_root}/icons/gorc/gorc-icon_sustainability.svg"
        },
        "engagement": {
            "icon": "{url_root}/icons/gorc/gorc-icon_engagement.svg"
        },
        "human-capacity": {
            "icon": "{url_root}/icons/gorc/gorc-icon_human-capacity.svg"
        },
        "interoperability": {
            "icon": "{url_root}/icons/gorc/gorc-icon_interoperability.svg"
        },
        "standards-conventions": {
            "icon": "{url_root}/icons/gorc/gorc-icon_standards-conventions.svg"
        },
        "ict-infrastructure": {
            "icon": "{url_root}/icons/gorc/gorc-icon_ict-infrastructure.svg"
        },
        "services-tools": {
            "icon": "{url_root}/icons/gorc/gorc-icon_services-tools.svg"
        },
        "research-objects": {
            "icon": "{url_root}/icons/gorc/gorc-icon_research-objects.svg"
        }
    }
}
```

### The data/json folder
The content of the `data/json` folder is copied to the output `model repository`. It is structured as a good example of a `model repository` could be without including a `root.json` file since the `root.json` is expected to be created using `converter/create_repo.py`.

A detailed specification of what a `model repository` consists of can be found in the documentation for [RDA GORC IM Visualization Tool](https://github.com/NBISweden/rda-gorc-im).

## Acknowledgments

This project is a part of [RDA GORC IM Visualization Tool](https://github.com/NBISweden/rda-gorc-im) and has received funding from the European Union’s Horizon Europe research and innovation programme under grant agreement No 101094406