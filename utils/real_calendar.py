"""
utils/real_calendar.py  —  JARVIS 3.0 REAL CALENDAR ACCESS
Reads and writes to the ACTUAL macOS Calendar and Reminders apps
using AppleScript. Never invents calendar events.
"""

import subprocess
import logging
from datetime import datetime

logger = logging.getLogger("JARVIS.real_calendar")


def _run_applescript(script: str) -> tuple[bool, str]:
    """
    Runs an AppleScript and returns (success, output_or_error).
    """
    try:
        result = subprocess.run(
            ["osascript", "-e", script],
            capture_output=True, text=True, timeout=12
        )
        if result.returncode == 0:
            return True, result.stdout.strip()
        else:
            return False, result.stderr.strip()
    except subprocess.TimeoutExpired:
        return False, "AppleScript timed out"
    except Exception as e:
        return False, str(e)


def get_todays_events() -> dict:
    """
    Reads REAL calendar events for today from the Calendar app.
    Returns actual event names and times — never invented data.
    """
    today = datetime.now().strftime("%B %d, %Y")   # e.g. "May 17, 2026"
    script = f'''
tell application "Calendar"
    set todayStart to (current date) - (time of (current date))
    set todayEnd to todayStart + (86399)
    set eventList to ""
    repeat with cal in calendars
        set calEvents to (events of cal whose start date >= todayStart and start date <= todayEnd)
        repeat with ev in calEvents
            set eventList to eventList & (summary of ev) & " at " & (start date of ev as string) & "\\n"
        end repeat
    end repeat
    return eventList
end tell
'''
    ok, output = _run_applescript(script)
    if ok:
        events = [e.strip() for e in output.strip().split("\n") if e.strip()]
        return {
            "ok"    : True,
            "date"  : today,
            "events": events,
            "count" : len(events),
            "source": "macOS Calendar app (AppleScript)",
        }
    return {
        "ok"   : False,
        "error": f"Cannot read Calendar. {output}. Grant Calendar access in System Preferences → Privacy → Calendars.",
        "source": "AppleScript",
    }


def get_events_for_date(date_str: str) -> dict:
    """
    Reads real calendar events for a specific date string (e.g. 'May 20, 2026').
    """
    script = f'''
tell application "Calendar"
    set targetDate to date "{date_str}"
    set dayStart to targetDate - (time of targetDate)
    set dayEnd to dayStart + 86399
    set eventList to ""
    repeat with cal in calendars
        set calEvents to (events of cal whose start date >= dayStart and start date <= dayEnd)
        repeat with ev in calEvents
            set eventList to eventList & (summary of ev) & " at " & (start date of ev as string) & "\\n"
        end repeat
    end repeat
    return eventList
end tell
'''
    ok, output = _run_applescript(script)
    if ok:
        events = [e.strip() for e in output.strip().split("\n") if e.strip()]
        return {"ok": True, "date": date_str, "events": events, "count": len(events), "source": "Calendar app"}
    return {"ok": False, "error": output, "source": "AppleScript"}


def create_event(title: str, date_str: str, duration_hours: float = 1.0, calendar_name: str = "") -> dict:
    """
    Creates a REAL calendar event that appears in the Calendar app.
    Returns whether it was actually created.
    """
    cal_clause = f'calendar "{calendar_name}"' if calendar_name else "calendar 1"
    script = f'''
tell application "Calendar"
    set eventStart to date "{date_str}"
    set eventEnd to eventStart + ({int(duration_hours * 3600)})
    make new event at {cal_clause} with properties {{summary:"{title}", start date:eventStart, end date:eventEnd}}
end tell
'''
    ok, output = _run_applescript(script)
    return {
        "ok"    : ok,
        "title" : title,
        "date"  : date_str,
        "error" : "" if ok else output,
        "source": "Calendar app (AppleScript)",
    }


def get_reminders() -> dict:
    """
    Reads REAL reminders from the macOS Reminders app.
    Never invents reminder content.
    """
    script = '''
tell application "Reminders"
    set reminderList to ""
    repeat with lst in lists
        set theReminders to (reminders of lst whose completed is false)
        repeat with r in theReminders
            set reminderList to reminderList & (name of r) & "\\n"
        end repeat
    end repeat
    return reminderList
end tell
'''
    ok, output = _run_applescript(script)
    if ok:
        items = [r.strip() for r in output.strip().split("\n") if r.strip()]
        return {
            "ok"     : True,
            "items"  : items,
            "count"  : len(items),
            "source" : "macOS Reminders app (AppleScript)",
        }
    return {
        "ok"   : False,
        "error": f"Cannot read Reminders. {output}. Grant access in System Preferences → Privacy → Reminders.",
        "source": "AppleScript",
    }


def add_reminder(title: str, list_name: str = "Reminders") -> dict:
    """Creates a REAL reminder that appears in the Reminders app."""
    script = f'''
tell application "Reminders"
    tell list "{list_name}"
        make new reminder with properties {{name:"{title}"}}
    end tell
end tell
'''
    ok, output = _run_applescript(script)
    return {
        "ok"   : ok,
        "title": title,
        "list" : list_name,
        "error": "" if ok else output,
        "source": "Reminders app (AppleScript)",
    }
