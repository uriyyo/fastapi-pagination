#!/usr/bin/env bash

set -ex

PYDANTIC_V2="${PYDANTIC_V2:-true}"
PYDANTIC_PRE_V2_12_5="${PYDANTIC_PRE_V2_12_5:-false}"
FASTAPI_PRE_0_112_4="${FASTAPI_PRE_0_112_4:-false}"
FASTAPI_PRE_0_137_0="${FASTAPI_PRE_0_137_0:-false}"
SYNC_EXTRA_ARGS=()
TEST_EXTRA_ARGS=()

if [[ "$PY_VERSION" == "3.14" ]]; then
    SYNC_EXTRA_ARGS+=(--no-extra ormar)
    TEST_EXTRA_ARGS+=(-m "not ormar")
fi

function _pip() {
    uv pip "$@" || true > /dev/null
}

function _pytest() {
    uv run --no-project pytest "$@"     \
      --cov=fastapi_pagination          \
      --cov-append                      \
      --cov-report=xml                  \
      "${TEST_EXTRA_ARGS[@]}"
}

function _restore_env() {
    uv sync --all-extras --dev "${SYNC_EXTRA_ARGS[@]}"
}

echo "Installing dependencies"
_restore_env

echo "Config: fastapi<0.112.4=$FASTAPI_PRE_0_112_4, fastapi<0.137.0=$FASTAPI_PRE_0_137_0, is-pydantic-v2=$PYDANTIC_V2"

if [[ "$FASTAPI_PRE_0_112_4" == true ]]; then
    _pip install "fastapi<0.112.4"
elif [[ "$FASTAPI_PRE_0_137_0" == true ]]; then
    _pip install "fastapi>=0.112.4,<0.137.0"
else
    _pip install -U "fastapi>=0.137.0"
fi

if [[ "$PYDANTIC_V2" == true && "$PYDANTIC_PRE_V2_12_5" == true ]]; then
    _pip install "pydantic>=2.0.0,<2.12.5"
elif [[ "$PYDANTIC_V2" == true ]]; then
    _pip install -U "pydantic>2.0.0"
else
  if [[ "$PY_VERSION" == "3.14" ]]; then
    echo "Skipping tests with Pydantic v1 on Python 3.14 due to incompatibilities"
    exit 0
  fi

  _pip install "pydantic<2"
fi

echo "Running unit-tests"
_pytest tests --ignore=tests/ext

echo "Running integration tests"
_pytest tests/ext

echo "Running tests with SQLAlchemy<2"
_pip install -U "sqlalchemy<2"
_pytest tests/ext -m "not sqlalchemy20"

echo "Restore env"
_restore_env
