#!/usr/bin/env bash

set -ex

CQL_TEST_HOST="${CQL_TEST_HOST:-localhost}"
PYDANTIC_V2="${PYDANTIC_V2:-true}"
FASTAPI_PRE_0_112_4="${FASTAPI_PRE_0_112_4:-false}"

function _pip() {
    poetry run pip "$@" || true > /dev/null
}

function _pytest() {
    poetry run pytest "$@"              \
      --cov=fastapi_pagination          \
      --cov-append                      \
      --cov-report=xml                  \
      --cassandra-dsn="${CQL_TEST_HOST}"
}

echo "Installing dependencies"
poetry install -E all --sync

echo "Config: fastapi<0.112.4=$FASTAPI_PRE_0_112_4, is-pydantic-v2=$PYDANTIC_V2"

if [[ "$FASTAPI_PRE_0_112_4" == true ]]; then
    _pip install "fastapi<0.112.4"
else
    _pip install -U "fastapi>=0.112.4"
fi

if [[ "$PYDANTIC_V2" == true ]]; then
    _pip install -U "pydantic>2.0.0"
else
    _pip install "pydantic<2"
fi

echo "Running unit-tests"
_pytest tests --ignore=tests/ext

echo "Running integration tests"
_pytest tests/ext

echo "Running tests with SQLAlchemy<2"
_pip install -U "sqlalchemy<2"
_pytest tests -m "not sqlalchemy20"

if [[ "$PYDANTIC_V2" == true ]]; then
    echo "Running ormar tests"
    _pip install -U ormar
    _pytest tests -m ormar
    _pip uninstall -y ormar
fi

echo "Running tests GINO tests"
_pip install -U "gino[starlette]"
_pytest tests -m gino
_pip uninstall -y gino

echo "Running orm tests"
_pip install "databases<0.9.0" orm
_pytest tests -m orm
_pip uninstall -y orm
