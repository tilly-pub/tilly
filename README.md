# tilly

CLI for easily creating Today I Learned posts.


## Installation

```
uv venv .venv
source .venv/bin/activate
uv pip install tilly
```

## Usage

Create a repo (or clone a repo from github):

```
git init
```

Add a TIL:

```
mkdir example # this will be the topic of your TIL.
echo "# My first TIL with tilly" > example/first-til.md
```

Commit your work:

```
git add .
git commit -m "adding first til"
```

Build the local `tils.db`:

```
tilly build
```

```
til hello
Hello from the TIL CLI!
```

or

```
$ tilly hello
Hello from the TIL CLI!
```

## Customize the default templates

Your can overwrite the default templates by first making a copy of the default templates:

```
tilly copy-templates
```

Change the templates to your liking, then generate your static site:

```
tilly gen-static --template-dir templates
```

Customized templates can also be served locally:

```
tilly serve --template-dir templates
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