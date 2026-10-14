import logging
import os
import sys
import time
from datetime import datetime

import pyodbc
from jira import JIRA
from dotenv import load_dotenv
from dateutil import parser as dateparser

load_dotenv()

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

PROJECT_KEY = "AS"
CLOSED_STATUSES = ("Declined", "Done", "Canceled", "Closed", "Completed", "Resolved")
BATCH_SIZE = 100  # hard stop of 100 from JIRA, default is 50 if not specified.
TABLE = "jira.Tickets"
COMMENTS_TABLE = "jira.TicketsComments"
COMMENT_PAGE_SIZE = 100

# Fields we actually need from Jira - keeps each API response small.
JIRA_FIELDS = "summary,description,created,resolutiondate,updated,assignee,reporter,creator,status,priority,issuetype"

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
)
log = logging.getLogger("jira_sync")


def require_env(name: str) -> str:
    value = os.environ.get(name)
    if not value:
        log.error("Missing required environment variable: %s", name)
        sys.exit(1)
    return value


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
# Helpers for pulling clean values out of Jira objects
# ---------------------------------------------------------------------------

def person_name(person_obj):
    """Return a display name for a Jira user field, or None if unset."""
    if person_obj is None:
        return None
    return getattr(person_obj, "displayName", None) or getattr(person_obj, "name", None)


def status_name(status_obj):
    if status_obj is None:
        return None
    return getattr(status_obj, "name", str(status_obj))


def priority_name(priority_obj):
    if priority_obj is None:
        return None
    return getattr(priority_obj, "name", str(priority_obj))


def issuetype_name(issuetype_obj):
    if issuetype_obj is None:
        return None
    return getattr(issuetype_obj, "name", str(issuetype_obj))


def parse_jira_dt(value):
    """Convert a Jira ISO8601 timestamp string into a real datetime, or None."""
    if not value:
        return None
    try:
        return dateparser.parse(value)
    except (ValueError, TypeError):
        log.warning("Could not parse Jira timestamp: %r", value)
        return None


def get_last_synced_id(cursor):
    """Resume from the highest IssueID already stored, if any."""
    cursor.execute(f"SELECT MAX(CAST(IssueID AS BIGINT)) FROM {TABLE}")
    row = cursor.fetchone()
    if row and row[0] is not None:
        return int(row[0])
    return 0


# ---------------------------------------------------------------------------
# Jira <-> SQL sync: issues
# ---------------------------------------------------------------------------

def build_jql(last_id: int) -> str:
    status_list = ", ".join(f'"{s}"' for s in CLOSED_STATUSES)
    if last_id:
        return (
            f"project = '{PROJECT_KEY}' AND id > {last_id} "
            f"AND status in ({status_list}) ORDER BY id ASC"
        )
    return (
        f"project = '{PROJECT_KEY}' AND status in ({status_list}) ORDER BY id ASC"
    )


def upsert_issue(cursor, issue) -> None:
    summary     = issue.fields.summary
    description = issue.fields.description
    created     = parse_jira_dt(issue.fields.created)
    resolved    = parse_jira_dt(issue.fields.resolutiondate)
    updated     = parse_jira_dt(issue.fields.updated)
    assignee    = person_name(issue.fields.assignee)
    priority    = priority_name(issue.fields.priority)
    reporter    = person_name(issue.fields.reporter)
    issuetype   = issuetype_name(issue.fields.issuetype)
    creator     = person_name(issue.fields.creator)
    status      = status_name(issue.fields.status)

    cursor.execute(f"SELECT 1 FROM {TABLE} WHERE IssueID = ?", issue.id)
    exists = cursor.fetchone() is not None

    if exists:
        update_sql = f"""
        UPDATE {TABLE}
        SET Summary = ?,
            Description = ?,
            Updated = ?,
            Assignee = ?,
            Priority = ?,
            Status = ?,
            IssueType = ?
        WHERE IssueID = ?
        """
        cursor.execute(
            update_sql,
            summary,
            description,
            updated,
            assignee,
            priority,
            status,
            issuetype,
            issue.id,
        )
        log.debug("Updated existing row for issue %s", issue.key)
    else:
        insert_sql = f"""
            INSERT INTO {TABLE}
                (JiraKey, IssueID, Summary, Description, Created, Resolved,
                 Updated, Assignee, Priority, Reporter, IssueType,
                 Creator, Status)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """
        cursor.execute(
            insert_sql,
            issue.key,
            issue.id,
            summary,
            description,
            created,
            resolved,
            updated,
            assignee,
            priority,
            reporter,
            issuetype,
            creator,
            status,
        )
        log.debug("Inserted new row for issue %s", issue.key)


# ---------------------------------------------------------------------------
# Jira <-> SQL sync: comments
# ---------------------------------------------------------------------------

def fetch_all_comments(jira_client, issue_key: str):
    """
    Pull every comment for an issue, paginating manually.

    The jira library's own `client.comments(issue)` only returns a single
    page (server default, often 50), so for tickets with a long comment
    history we page through the raw comment resource ourselves.
    """
    comments = []
    start_at = 0

    while True:
        # `_get_json` hits GET /rest/api/2/issue/{key}/comment directly so we
        # can control startAt/maxResults; the public `comments()` helper
        # doesn't expose pagination.
        payload = jira_client._get_json(
            f"issue/{issue_key}/comment",
            params={"startAt": start_at, "maxResults": COMMENT_PAGE_SIZE},
        )
        page = payload.get("comments", [])
        comments.extend(page)

        total = payload.get("total", len(comments))
        start_at += len(page)

        if not page or start_at >= total:
            break

    return comments


def upsert_comment(cursor, issue, comment: dict) -> None:
    comment_id = int(comment["id"])
    body       = comment.get("body")
    author     = (comment.get("author") or {}).get("displayName") or (comment.get("author") or {}).get("name")
    created    = parse_jira_dt(comment.get("created"))
    updated    = parse_jira_dt(comment.get("updated"))
    
    cursor.execute(f"SELECT 1 FROM {COMMENTS_TABLE} WHERE CommentID = {comment_id}")
    exists = cursor.fetchone() is not None

    if exists:
        update_sql = f"""
        UPDATE {COMMENTS_TABLE}
        SET Body = ?,
            AuthorName = ?,
            Updated = ?
        WHERE CommentID = ?
        """
        cursor.execute(update_sql, body, author, updated, comment_id)
        log.debug("Updated comment %s on issue %s", comment_id, issue.key)
    else:
        insert_sql = f"""
            INSERT INTO {COMMENTS_TABLE}
                (CommentID, IssueID, JiraKey, AuthorName, Body, Created, Updated)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """
        cursor.execute(
            insert_sql,
            comment_id,
            issue.id,
            issue.key,
            author,
            body,
            created,
            updated,
        )
        log.debug("Inserted comment %s on issue %s", comment_id, issue.key)


def sync_issue_comments(cursor, jira_client, issue) -> int:
    comments = fetch_all_comments(jira_client, issue.key)
    for comment in comments:
        upsert_comment(cursor, issue, comment)
    return len(comments)


# ---------------------------------------------------------------------------
# Main sync loop
# ---------------------------------------------------------------------------

def sync_closed_issues(jira_client, cnxn, cursor) -> tuple[int, int]:
    last_id = get_last_synced_id(cursor)
    log.info("Resuming sync after IssueID %s", last_id)

    total_synced = 0
    total_comments = 0
    start_at = 0

    while True:
        jql_query = build_jql(last_id)
        issues = jira_client.search_issues(
            jql_query,
            startAt=start_at,
            maxResults=BATCH_SIZE,
            fields=JIRA_FIELDS,
        )
        if not issues:
            break

        for issue in issues:
            try:
                upsert_issue(cursor, issue)
                comment_count = sync_issue_comments(cursor, jira_client, issue)
                cnxn.commit()
                total_synced += 1
                total_comments += comment_count
            except Exception:
                log.exception("Failed to sync issue %s (%s)", issue.key, issue.id)
                cnxn.rollback()

        log.info(
            "Synced batch of %d issues / %d comments so far (running totals: %d issues, %d comments)",
            len(issues), total_comments, total_synced, total_comments,
        )

        if len(issues) < BATCH_SIZE:
            break  # last page
        start_at += BATCH_SIZE

    return total_synced, total_comments


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------
def main():
    config = load_config()
    start_time = time.perf_counter()
    start_dt = datetime.now()
    log.info("Start time: %s", start_dt.strftime("%Y-%m-%d %H:%M:%S"))

    jira_client = JIRA(server=config["jira_url"], basic_auth=(config["jira_email"], config["jira_token"]))

    conn_str = (
        "DRIVER={SQL Server};"
        f"SERVER={config['sql_server']};"
        f"DATABASE={config['sql_database']};"
        f"UID={config['sql_username']};"
        f"PWD={config['sql_password']}"
    )

    total_synced = 0
    total_comments = 0

    with pyodbc.connect(conn_str) as cnxn:
        cursor = cnxn.cursor()
        try:
            while True:
                last_id_before = get_last_synced_id(cursor)

                synced, comments = sync_closed_issues(jira_client, cnxn, cursor)
                total_synced += synced
                total_comments += comments

                last_id_after = get_last_synced_id(cursor)

                if last_id_after == last_id_before:
                    log.info("last_id did not change (%s); nothing new to sync, stopping.", last_id_after)
                    break

                log.info("last_id advanced from %s to %s; running another pass.", last_id_before, last_id_after)
        finally:
            cursor.close()

    end_dt = datetime.now()
    elapsed_seconds = time.perf_counter() - start_time

    log.info("End time: %s", end_dt.strftime("%Y-%m-%d %H:%M:%S"))
    log.info("Issues synced: %d", total_synced)
    log.info("Comments synced: %d", total_comments)
    log.info("Elapsed: %.1f minutes (%.0f seconds)", elapsed_seconds / 60, elapsed_seconds)



if __name__ == "__main__":
    main()




