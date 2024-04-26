# ck-apstra-api


## prepare venv

```
uv venv
source .venv/bin/activate
uv pip install ck-apstra-api
```


## var/.env file example

```
apstra_server_host=local-apstra.pslab.link
apstra_server_port=443
apstra_server_username=admin
apstra_server_password=zaq1@WSXcde3$RFV
excel_input_file=./tests/fixtures/ApstraProvisiongTemplate.xlsx
config_yaml_input_file=tests/fixtures/config.yaml
logging_level=DEBUG
main_blueprint=terra
cabling_maps_yaml_file=tests/fixtures/sample-cabling-maps.yaml
```

Link the env file
```
ls -s var/.env .env
```

## run the commands

Help message
```
(venv) ckim@ckim-mbp:ck-apstra-api % ck-api --help                                                                         
Usage: ck-api [OPTIONS] COMMAND [ARGS]...

Options:
  --logging-level TEXT
  --help                Show this message and exit.

Commands:
  add-bp-from-json
  add-generic-systems
  add-ip-endpoints
  assign-connectivity-templates
  get-bp-into-json
  get-lldp-data                  Get LLDP data between managed switches
  import-routing-zones
  import-virtual-networks
  pull-device-configurations     pull produced configurations from Apstra
  read-generic-systems
(venv) ckim@ckim-mbp:ck-apstra-api % 
```
