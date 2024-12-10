#!/usr/bin/env bash

set -x

function is_docker_container_running() {
  docker ps -a --format '{{.Names}}' | grep -q "$1"
}

function wait_for_port() {
  echo "Waiting for port $1 to be open"

  port="$1"; shift
  retries="${1:-30}";

  while ! nc -z localhost "$port"; do
    sleep 1
    retries=$((retries - 1))
    if [[ "$retries" -le 0 ]]; then
      echo "Timeout waiting for port $port"
      exit 1
    fi
  done

  echo "Port $port is open"
}

DOCKER_NAME_PREFIX="${DOCKER_NAME_PREFIX:-fastapi-pagination}"

POSTGRES_NAME="${DOCKER_NAME_PREFIX}-postgres"
CASSANDRA_NAME="${DOCKER_NAME_PREFIX}-cassandra"
MONGO_NAME="${DOCKER_NAME_PREFIX}-mongo"

if ! is_docker_container_running "${POSTGRES_NAME}"; then
  echo "Starting PostgreSQL"

  POSTGRES_DB="${POSTGRES_DB:-postgres}"
  POSTGRES_USER="${POSTGRES_USER:-postgres}"
  POSTGRES_PASSWORD="${POSTGRES_PASSWORD:-postgres}"
  POSTGRES_VERSION="${POSTGRES_VERSION:-latest}"

  docker run -d -p 5432:5432                    \
    -e POSTGRES_DB="${POSTGRES_DB}"             \
    -e POSTGRES_USER="${POSTGRES_USER}"         \
    -e POSTGRES_PASSWORD="${POSTGRES_PASSWORD}" \
    --name="${POSTGRES_NAME}"                   \
    postgres:${POSTGRES_VERSION}
fi

if ! is_docker_container_running "${CASSANDRA_NAME}"; then
  echo "Starting ScyllaDB"

  docker run -d -p 9042:9042                    \
    --name="${CASSANDRA_NAME}"                  \
    scylladb/scylla:latest
fi

if ! is_docker_container_running "${MONGO_NAME}"; then
  echo "Starting MongoDB"

  docker run -d -p 27017:27017                  \
    --name="${MONGO_NAME}"                      \
    mongo:latest
fi

wait_for_port 5432
wait_for_port 9042
wait_for_port 27017
