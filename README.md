# tilly

CLI for easily creating Today I Learned posts.


## Installation

```
uv pip install tilly
```

## Usage

```
til hello
Hello from the TIL CLI!
```

or

```
$ tilly hello
Hello from the TIL CLI!
```

## Creating plugins

TODO

## Development, building and publishing

```
uv venv .venv --python=3.11
source .venv/bin/activate
uv pip install .
uv pip install -r requirements-dev.txt
./build.sh
./publish.sh
```