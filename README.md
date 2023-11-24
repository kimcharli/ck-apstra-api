# ck-apstra-api


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

```
ck-api read-generic-systems
```

```
ck-api add-generic-systems
```
