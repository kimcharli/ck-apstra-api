# Developer version of ck-apstra-api


## setup poetry

```sh
poetry config virtualenvs.in-project true
```

```sh
poetry export --without-hashes --format=requirements.txt > requirements.txt
```


## in case of uv venv

```
uv venv
source .venv/bin/activate
uv pip install ck-apstra-api
```


## run


```sh
poetry env info
```

```sh
poetry lock  
poetry install
poetry run pytest
```


```sh
poetry run python src/ck_apstra_api/generic_system.py
```

## pytest

```sh
poetry run pytest tests/test_20_generic_system.py 

poetry run pytest
```
