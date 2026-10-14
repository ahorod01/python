#pip install jira
import logging
#import jira
import os

from jira import JIRA
from dotenv import load_dotenv

load_dotenv()
# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------
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


# ---------------------------------------------------------------------------


   
# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------
       
jira_url = require_env("JIRA_URL")
email    = require_env("JIRA_EMAIL") 
token    = require_env("JIRA_API_TOKEN")

# Establish connection to Jira
jira = JIRA(server=jira_url, basic_auth=(email, token))

#list JIRA projects
projects = jira.projects() 
for project in projects: 
    print(f"{project.key}: {project.name}")

  


