#!/usr/bin/env bash

set -e

python -m unittest discover -v -s ./test

ruff check .
