# Developer version of ck-apstra-api


## setup with uv


```
uv init
uv add ...
```


## run


```sh
uv sync
uv run ck-cli
```


```sh
uv run python src/ck_apstra_api/generic_system.py
```

## pytest


## build and publish

uv publish was unstable
```
uv build
python -m twine upload dist/*
```

