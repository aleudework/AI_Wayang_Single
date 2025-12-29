# AI-Wayang-Single
A single-agent system for translating natural-language into executable Apache Wayang plans.

The system is implemented as a MCP server that can be connected to different MCP clients, for example a LLM chatbot. The system relies on a REST server using the Apache Wayang JSON-REST API for executing plans.

The system was developed as part of the Master Thesis "Agent-Based Systems for Apache Wayang Plan". For a deeper understanding of the system, we recommend reading the thesis report.

# Start
Start the MCP server by running the main.py file.

The server starts by default on port 9500.

# Requirements
The following components are required to run the system:

- A JSON-REST API server
- A MCP client to invoke the MCP server (can also be a client testing tool)
- An OpenAI API Key
- Python with listed dependencies below

# Setup

## Python and Python Dependencies
Python 3.12.4 is recommended, as this version has been tested.

All required Python dependencies can be found in the requirements.txt file.

## .env File
You must create a .env file with the following required variables.

**Required**

OPENAI_API_KEY: API Key to LLMs
WAYANG_URL: URL to JSON-REST server for plan exection

JDBC_URI: JDBC connection string
JDBC_USERNAME: Username
JDBC_PASSWORD: Password

OR/AND:

INPUT_FOLDER: Path to .txt input files

**Not required, but recommended:**

LOG_FOLDER: Path for session logs

OUTPUT_FOLDER: Path to preferred location for .txt files

BUILDER_LLM: Preferred GPT-model for Builder Agent
BUILDER_REASON_EFFORT: Reasoning level for the agent

USE_DEBUGGER: Boolean to enable/disable debugging
DEBUGGER_LLM: Preffered GPT-model for Debugger Agent
DEBUGGER_REASON_EFFORT: Reasoning level for the agent

# Recommendation
We recommend generating schemas for your data sources. Preferredably using the "load_schemas" tool during server initialization.