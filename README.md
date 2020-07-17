# watchfor
CLI application for monitoring online services

## Installation:
```
git clone 'https://github.com/tru-software/watchfor'
cd watchfor
virtualenv -p python3.8 venv
./venv/bin/pip install -r requirements.txt
./venv/bin/python -m watchfor check -d ./tests/data1/
```

## Run checks
```
./venv/bin/python -m watchfor check -d ./tests/data1/
```

## Tests:
```
./venv/bin/ptw watchfor -- watchfor/tests
```