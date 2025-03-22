#!/usr/bin/env bash

set -ex

PYDANTIC_V2="${PYDANTIC_V2:-true}"
FASTAPI_PRE_0_112_4="${FASTAPI_PRE_0_112_4:-false}"

function _pip() {
    uv pip "$@" || true > /dev/null
}

function _pytest() {
    uv run --no-project pytest "$@"     \
      --cov=fastapi_pagination          \
      --cov-append                      \
      --cov-report=xml
}

function _restore_env() {
    uv sync --all-extras --dev
}

echo "Installing dependencies"
_restore_env

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

# install greenlet for python 3.13 separately
if [[ "$PY_VERSION" == "3.13" ]]; then
  _pip install greenlet
fi

echo "Running integration tests"
_pytest tests/ext

echo "Running tests with SQLAlchemy<2"
_pip install -U "sqlalchemy<2"
_pytest tests/ext -m "not sqlalchemy20"

if [[ "$PYDANTIC_V2" == true ]]; then
    echo "Running ormar tests"
    _pip install -U ormar
    _pytest tests/ext -m ormar
    _pip uninstall ormar
fi

echo "Running orm tests"
_pip install "databases<0.9.0" orm
_pytest tests/ext -m orm
_pip uninstall orm

if [[ "$PYDANTIC_V2" == true ]]; then
  echo "Running tests GINO tests"
  _pip install -U "gino[starlette]" "sqlalchemy<1.4" "asyncpg"
  _pytest tests -m gino
  _pip uninstall gino gino-starlette
fi

echo "Restore env"
_restore_env
