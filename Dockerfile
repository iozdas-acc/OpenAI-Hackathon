FROM python:3.12.6

RUN apt-get update

RUN apt-get install -y build-essential checkinstall wget nano sudo git-lfs bash-completion

RUN useradd -ms /bin/bash trainer

# Install Node.js 20 LTS (replaces the basic nodejs/npm install)
RUN curl -fsSL https://deb.nodesource.com/setup_20.x | bash - \
    && apt-get install -y nodejs

RUN apt-get install -y python3 python3-pip
RUN npm install -g configurable-http-proxy
RUN pip3 install jupyterhub

RUN pip3 install --upgrade jupyterlab
RUN pip3 install --upgrade notebook

RUN pip install langchain==0.2 sentence-transformers==2.6.1 pandas openpyxl faiss-cpu==1.8.0
RUN pip install langchain-community==0.0.20

RUN curl -s https://ngrok-agent.s3.amazonaws.com/ngrok.asc | sudo tee /etc/apt/trusted.gpg.d/ngrok.asc >/dev/null \
    && echo "deb https://ngrok-agent.s3.amazonaws.com buster main" | sudo tee /etc/apt/sources.list.d/ngrok.list \
    && sudo apt update && sudo apt install -y ngrok

RUN curl -fsSL https://code-server.dev/install.sh | sh

RUN pip install streamlit ollama

RUN apt-get install -y apt-transport-https ca-certificates gnupg curl
RUN curl https://packages.cloud.google.com/apt/doc/apt-key.gpg | sudo gpg --dearmor -o /usr/share/keyrings/cloud.google.gpg
RUN echo "deb [signed-by=/usr/share/keyrings/cloud.google.gpg] https://packages.cloud.google.com/apt cloud-sdk main" \
    | sudo tee -a /etc/apt/sources.list.d/google-cloud-sdk.list
RUN apt-get update && sudo apt-get install -y google-cloud-cli

# Install OpenAI Codex CLI globally
RUN npm install -g @openai/codex

# Install MCP-related global packages for VS Code / code-server
RUN npm install -g \
    @modelcontextprotocol/server-filesystem \
    @modelcontextprotocol/server-github \
    @modelcontextprotocol/server-memory \
    @modelcontextprotocol/inspector

RUN apt-get update && apt-get install -y postgresql-client

RUN pip install postgres-mcp uv google-cloud-bigquery

RUN pip install oracledb "mcp[cli]" fastmcp


WORKDIR /hackathon
COPY setup_env.sh /hackathon/setup_env.sh
COPY services/mcp /hackathon/services/mcp
COPY vscode_extensions /hackathon/vscode_extensions

RUN umask 002

ENTRYPOINT ["/bin/bash", "setup_env.sh"]
LABEL version="1.0.0"
