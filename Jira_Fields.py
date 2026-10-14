import requests
from requests.auth import HTTPBasicAuth
import json
import logging
import os
from jira import JIRA

from dotenv import load_dotenv

load_dotenv()

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------


# Fields we actually need from Jira - keeps each API response small.
JIRA_FIELDS = "summary,description,created,updated,assignee,reporter,creator,status"

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
)
log = logging.getLogger("jira_sync")


def require_env(name: str) -> str:
    #values set in .env file
    value = os.environ.get(name)
    if not value:
        log.error("Missing required environment variable: %s", name)
        sys.exit(1)
    return value

#config dictionary
def load_config():
    return {
        "jira_url":     require_env("JIRA_URL"),
        "jira_email":   require_env("JIRA_EMAIL"),
        "jira_token":   require_env("JIRA_API_TOKEN"),
        "sql_server":   require_env("SQL_SERVER"),
        "sql_database": require_env("SQL_DATABASE"),
        "sql_username": require_env("SQL_USERNAME"),
        "sql_password": require_env("SQL_PASSWORD"),
    }
# ---------------------------------------------------------------------------



# --- Configuration ---
JIRA_URL = require_env("JIRA_URL")
EMAIL = require_env("JIRA_EMAIL")
API_TOKEN = require_env("JIRA_API_TOKEN")  # Create at https://id.atlassian.com/manage-profile/security/api-tokens

# --- Fetch all fields ---
url = f"{JIRA_URL}/rest/api/3/field"

response = requests.get(
    url,
    auth=HTTPBasicAuth(EMAIL, API_TOKEN),
    headers={"Accept": "application/json"}
)

response.raise_for_status()
fields = response.json()

# --- Print all fields (id, name, custom?) ---
for field in fields:
    print(f"{field['id']:25} | custom={str(field['custom']):5} | {field['name']}")

# --- Search for a specific field by name (e.g. "Request Type") ---
search_term = "request type"
matches = [f for f in fields if search_term in f["name"].lower()]

print("\nMatches for:", search_term)
for m in matches:
    print(json.dumps(m, indent=2))
