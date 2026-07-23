#!/usr/bin/env bash

set -ex

DEPS="${DEPS:-latest}"
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

echo "Config: deps=$DEPS"

if [[ "$DEPS" == lowest ]]; then
    _pip install "fastapi==0.137.0" "pydantic==2.12.5"
else
    _pip install -U fastapi pydantic
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
