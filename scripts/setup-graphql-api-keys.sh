#!/bin/bash
#
# setup-graphql-api-keys.sh — Manage GraphQL org1 API keys in AWS SSM Parameter Store
#
# Creates two SSM parameters:
#   1. Server-side: /{env}/graphql-org1/ApiKeys  (format: "key:client-name")
#   2. Client-side: /{env}/semantic-search/GraphqlApiKey  (bare key)
#
# Usage:
#   AWS_PROFILE=lif ./scripts/setup-graphql-api-keys.sh <env>           # Preview
#   AWS_PROFILE=lif ./scripts/setup-graphql-api-keys.sh <env> --apply   # Create/update
#
# Examples:
#   AWS_PROFILE=lif ./scripts/setup-graphql-api-keys.sh demo
#   AWS_PROFILE=lif ./scripts/setup-graphql-api-keys.sh demo --apply
#   AWS_PROFILE=lif ./scripts/setup-graphql-api-keys.sh dev --apply

set -euo pipefail

# ----------- Configuration -----------

GRAPHQL_SERVICE_NAME="graphql-org1"
CLIENT_SERVICE_NAME="semantic-search"
CLIENT_LABEL="semantic-search"

# ----------- Argument parsing -----------

ENV="${1:-}"
APPLY=false

if [[ -z "$ENV" ]]; then
    echo "Usage: $0 <env> [--apply]"
    echo ""
    echo "  <env>      Environment name (e.g., dev, demo)"
    echo "  --apply    Actually create/update SSM parameters (default: preview only)"
    exit 1
fi

shift
while [[ $# -gt 0 ]]; do
    case "$1" in
        --apply)
            APPLY=true
            shift
            ;;
        *)
            echo "Unknown option: $1"
            exit 1
            ;;
    esac
done

# ----------- SSM parameter paths -----------

SERVER_PARAM="/${ENV}/${GRAPHQL_SERVICE_NAME}/ApiKeys"
CLIENT_PARAM="/${ENV}/${CLIENT_SERVICE_NAME}/GraphqlApiKey"

# ----------- Helper functions -----------

generate_key() {
    python3 -c "import secrets; print(secrets.token_urlsafe(32))"
}

get_ssm_param() {
    local param_name="$1"
    aws ssm get-parameter \
        --name "$param_name" \
        --with-decryption \
        --query "Parameter.Value" \
        --output text 2>/dev/null || echo ""
}

put_ssm_param() {
    local param_name="$1"
    local param_value="$2"
    local description="$3"

    aws ssm put-parameter \
        --name "$param_name" \
        --value "$param_value" \
        --type "SecureString" \
        --description "$description" \
        --overwrite
}

# ----------- Main logic -----------

echo "=== GraphQL API Key Setup ==="
echo "Environment: ${ENV}"
echo "Server param: ${SERVER_PARAM}"
echo "Client param: ${CLIENT_PARAM}"
echo ""

# Check existing state
existing_server_value=$(get_ssm_param "$SERVER_PARAM")
existing_client_value=$(get_ssm_param "$CLIENT_PARAM")

if [[ -n "$existing_client_value" ]]; then
    echo "Existing client key found in ${CLIENT_PARAM}"
    KEY="$existing_client_value"
    echo "  Will reuse existing key"
else
    echo "No existing client key found — will generate a new one"
    KEY=$(generate_key)
    echo "  Generated key: ${KEY:0:8}..."
fi

# Build the server-side value (format: "key:client-name")
NEW_ENTRY="${KEY}:${CLIENT_LABEL}"

if [[ -n "$existing_server_value" ]]; then
    echo ""
    echo "Existing server ApiKeys value found in ${SERVER_PARAM}"
    # Check if our client label already has an entry
    if echo "$existing_server_value" | grep -q ":${CLIENT_LABEL}"; then
        echo "  Entry for '${CLIENT_LABEL}' already exists — will replace it"
        # Remove existing entry for this client and append updated one
        UPDATED_VALUE=$(echo "$existing_server_value" | tr ',' '\n' | grep -v ":${CLIENT_LABEL}$" | tr '\n' ',' | sed 's/,$//')
        if [[ -n "$UPDATED_VALUE" ]]; then
            SERVER_VALUE="${UPDATED_VALUE},${NEW_ENTRY}"
        else
            SERVER_VALUE="${NEW_ENTRY}"
        fi
    else
        echo "  Appending new entry for '${CLIENT_LABEL}'"
        SERVER_VALUE="${existing_server_value},${NEW_ENTRY}"
    fi
else
    echo "No existing server ApiKeys — will create with single entry"
    SERVER_VALUE="${NEW_ENTRY}"
fi

echo ""
echo "--- Planned changes ---"
echo "Server ${SERVER_PARAM}:"
echo "  Value: ${SERVER_VALUE}"
echo ""
echo "Client ${CLIENT_PARAM}:"
echo "  Value: ${KEY:0:8}..."
echo ""

if [[ "$APPLY" != "true" ]]; then
    echo "DRY RUN — pass --apply to create/update parameters"
    exit 0
fi

echo "Applying..."
echo ""

put_ssm_param "$SERVER_PARAM" "$SERVER_VALUE" "GraphQL org1 API keys (key:client-name format)"
echo "  Created/updated: ${SERVER_PARAM}"

put_ssm_param "$CLIENT_PARAM" "$KEY" "GraphQL API key for ${CLIENT_SERVICE_NAME}"
echo "  Created/updated: ${CLIENT_PARAM}"

echo ""
echo "Done. Redeploy affected services to pick up the new keys:"
echo "  ./aws-deploy.sh -s ${ENV} --only-stack ${ENV}-lif-semantic-search"
echo "  ./aws-deploy.sh -s ${ENV} --only-stack ${ENV}-lif-graphql-org1"
