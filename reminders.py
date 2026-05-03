import re
from datetime import datetime, timedelta, time as dtime
from zoneinfo import ZoneInfo

IST = ZoneInfo("Asia/Kolkata")

def parse_reminder_time(text: str):
    """
    Parses natural language time from text.
    Returns:
        - datetime (absolute time)
        - timedelta (relative duration)
        - None (if no time found)
    
    Supported formats:
        Relative: 10m, 10min, 10 minutes, in 10 mins, 2h, 2hr, 2 hours, 30s, 30sec
        Absolute: 5pm, 5:30pm, at 5pm, at 5:30 pm, at 17:00
    """
    text = text.lower().strip()
    now = datetime.now(IST)

    # 1. Check relative time (e.g., "in 10 mins", "10m", "2h", "30s")
    # Handles shorthand: m, min, mins, minute, minutes, h, hr, hrs, hour, hours, s, sec, secs, second, seconds
    rel_pattern = r'(?:in\s+)?(\d+)\s*(m(?:in(?:ute)?s?)?|h(?:(?:ou)?rs?)?|s(?:ec(?:ond)?s?)?)(?:\b|$)'
    match = re.search(rel_pattern, text)
    if match:
        amount = int(match.group(1))
        unit = match.group(2)
        
        if unit.startswith('m'):
            return timedelta(minutes=amount)
        elif unit.startswith('h'):
            return timedelta(hours=amount)
        elif unit.startswith('s'):
            return timedelta(seconds=amount)

    # 2. Check absolute time with "at" prefix (e.g., "at 5:30 pm", "at 17:00")
    abs_pattern = r'at\s+(\d{1,2})(?::(\d{2}))?\s*(am|pm)?'
    match = re.search(abs_pattern, text)
    if match:
        hour = int(match.group(1))
        minute = int(match.group(2) or 0)
        meridiem = match.group(3)

        if meridiem:
            if meridiem == "pm" and hour < 12:
                hour += 12
            elif meridiem == "am" and hour == 12:
                hour = 0
        
        target_time = now.replace(hour=hour, minute=minute, second=0, microsecond=0)
        if target_time < now:
            target_time += timedelta(days=1)
        return target_time

    # 3. Check bare absolute time without "at" (e.g., "5pm", "5:30pm", "17:00")
    bare_abs_pattern = r'^(\d{1,2})(?::(\d{2}))?\s*(am|pm)$'
    match = re.search(bare_abs_pattern, text)
    if match:
        hour = int(match.group(1))
        minute = int(match.group(2) or 0)
        meridiem = match.group(3)

        if meridiem:
            if meridiem == "pm" and hour < 12:
                hour += 12
            elif meridiem == "am" and hour == 12:
                hour = 0
        
        target_time = now.replace(hour=hour, minute=minute, second=0, microsecond=0)
        if target_time < now:
            target_time += timedelta(days=1)
        return target_time

    return None
