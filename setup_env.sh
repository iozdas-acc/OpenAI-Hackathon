#!/usr/bin/env bash
readonly REQUIREMENTS_DIRECTORY="/tmp"
readonly SCRIPT_DIRECTORY=$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)

function main() {
  echo "Install JupyterHub."
  echo "Install dependencies from ${REQUIREMENTS_DIRECTORY}"

  set -o errexit
  set -o pipefail
  set -o nounset
  set -o errtrace
  install_env
}

function install_env() {

  echo -e "hackathon\nhackathon" | passwd trainer
  usermod -aG sudo trainer

  echo "[*] Printing Path..."
  echo "$PATH"

  echo "[*] Printing Python Version..."
  python3 -V

  echo "[*] Printing Node.js Version..."
  node -v
  npm -v

  # Install Copilot extension
#   code-server --install-extension vscode_extensions/GitHub.copilot-1.208.963.vsix
    code-server --install-extension vscode_extensions/openai.chatgpt-26.5409.20454.vsix
#   code-server --install-extension GitHub.copilot
    # code-server --install-extension openai.chatgpt

  # Configure MCP servers for code-server (written to the trainer user's config)
  setup_mcp_config
  setup_mcp_postgres
  setup_mcp_bigquery
  setup_mcp_oracle

  code-server --bind-addr 0.0.0.0:8080 &

  echo "[*] Starting Jupyter Application..."
  jupyterhub
}

function setup_mcp_postgres() {
  echo "[*] Configuring Postgres MCP for Codex..."
  codex mcp add postgres -- sh -c "python -m postgres_mcp \"postgresql://${POSTGRES_USER}:${POSTGRES_PASSWORD}@${POSTGRES_HOST}:${POSTGRES_PORT}/${POSTGRES_DB}\" --access-mode=unrestricted --transport=stdio"
}

function setup_mcp_bigquery() {
  echo "[*] Configuring BigQuery MCP for Codex..."
  codex mcp add bigquery -- sh -c "npx -y @ergut/mcp-bigquery-server \
    --project-id=${GOOGLE_CLOUD_PROJECT} \
    --location=US \
    --api-endpoint=http://${BIGQUERY_EMULATOR_HOST}"
}


function setup_mcp_oracle() {
  local port="${ORACLE_PORT:-1521}"
  local script="${ORACLE_MCP_SCRIPT:-/hackathon/services/mcp/oracle_mcp_server.py}"

  if [[ -z "$ORACLE_USER" || -z "$ORACLE_PASSWORD" || -z "$ORACLE_HOST" || -z "$ORACLE_SERVICE" ]]; then
    echo "[!] Set ORACLE_USER, ORACLE_PASSWORD, ORACLE_HOST, and ORACLE_SERVICE first."
    return 1
  fi

  if [[ ! -f "$script" ]]; then
    echo "[!] Oracle MCP script not found at: $script"
    return 1
  fi

  local dsn="${ORACLE_USER}/${ORACLE_PASSWORD}@${ORACLE_HOST}:${port}/${ORACLE_SERVICE}"

  echo "[*] Configuring Oracle MCP for Codex..."
  codex mcp add oracle -- \
    sh -c "python \"${script}\" \"${dsn}\" --access-mode=unrestricted --transport=stdio"

  echo "[✓] Oracle MCP registered. DSN: ${ORACLE_USER}@${ORACLE_HOST}:${port}/${ORACLE_SERVICE}"
}




function setup_mcp_config() {
  echo "[*] Configuring MCP servers for code-server..."

  # code-server stores settings in ~/.local/share/code-server/User/
  MCP_CONFIG_DIR="/home/trainer/.local/share/code-server/User"
  mkdir -p "$MCP_CONFIG_DIR"

  # Write MCP server definitions into VS Code settings.json
  cat > "$MCP_CONFIG_DIR/settings.json" <<'EOF'
{
  "mcp.servers": {
    "filesystem": {
      "command": "npx",
      "args": ["-y", "@modelcontextprotocol/server-filesystem", "/home/trainer"],
      "description": "Access local filesystem under /home/trainer"
    },
    "memory": {
      "command": "npx",
      "args": ["-y", "@modelcontextprotocol/server-memory"],
      "description": "Persistent memory store across sessions"
    },
    "github": {
      "command": "npx",
      "args": ["-y", "@modelcontextprotocol/server-github"],
      "env": {
        "GITHUB_PERSONAL_ACCESS_TOKEN": "${env:GITHUB_TOKEN}"
      },
      "description": "GitHub MCP server — set GITHUB_TOKEN env var"
    }
  },
  "terminal.integrated.env.linux": {
    "OPENAI_API_KEY": "${env:OPENAI_API_KEY}"
  }
}
EOF

  chown -R trainer:trainer /home/trainer/.local
  echo "[*] MCP config written to $MCP_CONFIG_DIR/settings.json"
}

main
