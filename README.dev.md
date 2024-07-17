# Developer version of ck-apstra-api


## setup poetry

```sh
poetry config virtualenvs.in-project true
```

```sh
poetry export --without-hashes --format=requirements.txt > requirements.txt
```


```
poetry init
poetry add ck-apstra-api
```


## run


```sh
poetry env info
```

```sh
poetry lock  
poetry install
poetry run pytest
poetry run ck-cli
```


```sh
poetry run python src/ck_apstra_api/generic_system.py
```

## pytest

```sh
poetry run pytest tests/test_20_generic_system.py 

poetry run pytest
```
