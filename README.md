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

## Installation & usage

#### 1. Install `watchfor` in your local python virtual enviroment:

```bash
python3 -m venv ./watchforapp
./watchforapp/bin/pip install -e 'git+https://github.com/tru-software/watchfor#egg=watchfor'
```

#### 2. Create a simple configuration

> :+1: Configuration directories are designed to be under repository version control, like a `git`.

```bash
mkdir ~/my_services
git init ~/my_services  # optional, or just put this directory under repo and commit&push configs
```

Create a config file for **service** `~/my_services/github.com.yml` and fill with a following content (YAML format):
```yml
schema: 1
host: github.com
method: GET
protocol: https
timeout: 10.0
headers:
  accept-encoding: gzip, deflate, br
  accept-language: pl,en-US;q=0.9,en;q=0.8
  accept: text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8
  user-agent: Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/83.0.4103.116 Safari/537.36
checks:
  - request: /
    response:
      - ValidResponse
```

The above configuration tests a `http://github.com` site, checks only a main page `/` and expects a valid http response. See `tests/data1` for more examples and a documentation (will be available soon) for all options.

#### 3. Test your configuration

```bash
./watchforapp/bin/watchfor debug -d ~/my_services/
```

The response should look as follow:

![watchfor debug](assets/Screenshot_20200723_115951.jpeg)

#### 4. Setup MTA - a mailing gateway

MTA configuration is defined in `_mta.yml` file in your configuration directory. The content of this file looks as follow (YAML format):
```yml
host: "smtp.gmail.com"
port: 587
user: "your-gmail-user@gmail.com"
password: "xxx-xxx"
ssl: false
tls: true
from: "your-gmail-user@gmail.com"
receivers:
 - "your@email.net"
 - "another.admin@email.net"
```

> :zap: TODO: configuration for a local `sendmail`.

#### 5. Run PRODUCTION checks

> :zap: TODO: configuration for `crontab`

---

This one reads all configurations from a directory `~/my_services/` (`*.yml` files), runs all checks and store results in a file `/tmp/watchfor-my_services.pickle` (python pickle format). In case of failure an email is send according to setup from `_mta.yml`.

```
./watchforapp/bin/watchfor check -d ~/my_services/ -s /tmp/watchfor-my_services.pickle
```

> :+1: Results file (`-s` parameter) keeps latest statuses to prevent spam in the notifications - too much emails in case of longer service downtime/failure. For one long service failure only one email is issued for each day.

---

This one reads all configurations from a directory `~/my_services/` (`*.yml` files), runs all checks and store results in a file `/tmp/watchfor-my_services.pickle` (python pickle format).
In case of failure an email is send according to setup from `_mta.yml`.
Additionally all results are stored in the `/tmp/watchfor-my_services.html`.

```
./watchforapp/bin/watchfor check -d ~/my_services/ -s /tmp/watchfor-my_services.pickle -o /tmp/watchfor-my_services.html
```

## Installation for a development

Clone `watchfor` in your local python virtualenv:

```bash
git clone 'https://github.com/tru-software/watchfor'
cd watchfor
python3 -m venv ./venv
./venv/bin/pip install -r requirements.txt
./venv/bin/pip install -r requirements-dev.txt
```

##### Run `debug` for sample configuration:
```bash
./venv/bin/python -m watchfor debug -d ./tests/data1/
```

##### Run unit-tests (`pytest`) only once:
```bash
./venv/bin/pytest watchfor/tests
```

##### Run unit-tests (`pytest` + `pytest-watch`) after each code change (auto reload):
```bash
./venv/bin/ptw watchfor -- watchfor/tests
```

##### Run `debug` after each code change (auto reload with `watchdog`)
```bash
./venv/bin/watchmedo auto-restart --ignore-directories --recursive -d . -p '*.py;*.
mako;*.yml' -- ./venv/bin/python -m watchfor debug -d ./tests/data1/
```
