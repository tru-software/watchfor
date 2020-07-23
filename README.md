# watchfor

CLI application for monitoring online services

## Features
* checks responses of the HTTP/HTTPS services
* YAML configuration
* notifications via emails in case of failure
* debuging tool for configuration tests
* HTTP headers validation
* HTTP status validation
* parsing HTML/XML
* images validation
* robots.txt validation

## Installation

##### 1. Install `watchfor` in your local python virtual enviroment:

```bash
python3 -m venv ./watchforapp
./watchforapp/bin/pip install -e 'git+https://github.com/tru-software/watchfor#egg=watchfor'
```

##### 2. Create a simple configuration

> :+1: Configuration directories are designed to be under repository version control, like `git`.

```bash
mkdir ~/my_services
git init ~/my_services  # optional, or just put this directory under repo
```

Create a file `~/my_services/github.com.yml` with your favorite editor and fill with a following content:
```yml
schema: 1
host: github.com
method: GET
protocol: https
timeout: 10.0
headers:
  accept-encoding: gzip, deflate, br
  accept-language: pl,en-US;q=0.9,en;q=0.8
  accept: text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9
  user-agent: Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/83.0.4103.116 Safari/537.36
checks:
  - request: /
    response:
      - ValidResponse
```


```bash
cd watchfor
virtualenv -p python3.8 venv
./venv/bin/pip install -r requirements.txt
```

./venv/bin/python -m watchfor check -d ./tests/data1/./venv/bin/python -m watchfor check -d ./tests/data1/

## Run checks

```
./venv/bin/python -m watchfor check -d ./tests/data1/
```

## Installation for development

Install `watchfor` in your local python virtualenv:

```bash
git clone 'https://github.com/tru-software/watchfor'
cd watchfor
virtualenv -p python3.8 venv
./venv/bin/pip install -r requirements.txt
```

./venv/bin/python -m watchfor check -d ./tests/data1/./venv/bin/python -m watchfor check -d ./tests/data1/


## Tests

```
./venv/bin/ptw watchfor -- watchfor/tests
```
