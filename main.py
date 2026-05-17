"""
main.py  —  JARVIS 3.0 REAL ACCESS EDITION
All llm calls return dicts with reply/confidence/sources.
Real data sources checked before use. Honest errors always.
"""
import sys, threading, time, logging, datetime, re
from PyQt6.QtWidgets import QApplication

logging.basicConfig(filename="jarvis_log.txt", level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")
logger = logging.getLogger("JARVIS.main")
JARVIS_VERSION = "3.0-RealAccess"

import memory.database      as db
import voice.speaker        as speaker
import voice.listener       as listener
import brain.llm            as llm
from agents.master_agent    import master
import system.mac_control   as mac
import automation.modes     as modes
import vision.screen_reader as screen_reader
import utils.internet       as internet
import utils.real_files     as real_files
import utils.real_system    as real_system
import utils.real_calendar  as real_calendar
import memory.rag           as rag
import core.real_access     as ra
from ui.hud import CinematicHUD

hud: CinematicHUD | None = None


def _set_state(s):
    if hud: hud.sig_state.emit(s)


def _say_result(result: dict):
    """Emit AI dict (reply/confidence/sources) to HUD and speak."""
    reply      = result.get("reply", "I encountered an error.")
    confidence = result.get("confidence", 0)
    sources    = result.get("sources", [])
    if hud:
        hud.sig_update_ai.emit(reply)
        hud.sig_confidence.emit(confidence)
        hud.sig_sources.emit(sources)
    _set_state("speaking")
    speaker.speak(reply)
    _set_state("idle")


def _say(text, confidence=80, sources=None):
    if hud:
        hud.sig_update_ai.emit(text)
        hud.sig_confidence.emit(confidence)
        hud.sig_sources.emit(sources or ["Direct system access"])
    _set_state("speaking")
    speaker.speak(text)
    _set_state("idle")


def _error(msg):
    if hud: hud.sig_error.emit(msg)
    speaker.speak(msg)
    _set_state("idle")


def execute_command(command: str):
    """Routes all voice commands to real data sources with honest error handling."""
    if not command: return
    if hud: hud.sig_update_user.emit(command)
    try: db.auto_extract_facts(command)
    except Exception: pass
    lower = command.lower()
    _set_state("thinking")
    try:
        # Goodbye
        if any(w in lower for w in ["goodbye jarvis","shutdown jarvis","exit jarvis"]):
            _say("Goodbye, Sir.", 100, ["Session control"])
            llm.clear_session(); time.sleep(1); QApplication.quit(); return

        # Open app
        if "open" in lower and "mode" not in lower and "website" not in lower and "file" not in lower:
            m = re.search(r'open\s+([a-zA-Z0-9 ]+?)(?:\s+and|\s*$)', lower)
            if m: _say(mac.open_app(m.group(1).strip().title()), 100, ["macOS open"]); return

        # Open website
        if "open website" in lower or "go to" in lower:
            m = re.search(r'(?:open website|go to)\s+(\S+)', lower)
            if m: _say(mac.open_website(m.group(1)), 100, ["macOS open"]); return

        # Close app
        if lower.startswith("close "):
            _say(mac.close_app(lower.replace("close","").strip().title()), 100, ["AppleScript"]); return

        # Volume
        if "volume" in lower:
            if "mute" in lower:   _say(mac.mute(),100,["AppleScript"]); return
            if "unmute" in lower: _say(mac.unmute(),100,["AppleScript"]); return
            nums = re.findall(r'\d+', lower)
            _say(mac.set_volume(int(nums[0])) if nums else "Specify level.", 100, ["AppleScript"]); return

        # Real system stats
        if any(kw in lower for kw in ["system stats","cpu usage","ram usage","disk space","memory usage"]):
            _say(real_system.full_stats_summary(), 100, ["psutil (live kernel)"]); return

        if "battery" in lower:
            info = real_system.battery_info()
            if info["ok"]:
                plug = "charging" if info["plugged_in"] else f"on battery — {info['time_left']} left"
                _say(f"Battery: {info['percent']}%, {plug}.", 100, [info["source"]])
            else: _error(info.get("error","Cannot read battery.")); return

        # Read real file
        if "read file" in lower or "open file" in lower:
            m = re.search(r'(?:read|open) file\s+(.+)', lower)
            if m:
                result = real_files.read_file(m.group(1).strip())
                if result["ok"]:
                    ai = llm.generate_response(f"Summarise this file: {result['content'][:1500]}")
                    ai["sources"] = [f"Real file: {result.get('path','')}"] + ai.get("sources",[])
                    _say_result(ai)
                else: _error(result["error"])
            return

        # Find file (real Spotlight)
        if "find file" in lower:
            fname = re.sub(r'find file','',lower).strip()
            paths = real_files.spotlight_search(fname)
            if paths: _say(f"Found {len(paths)}: {'; '.join(paths[:3])}", 100, ["Spotlight mdfind"])
            else: _say(f"No file matching '{fname}' found.", 100, ["Spotlight mdfind"])
            return

        # Run terminal command (real)
        if lower.startswith("run command") or lower.startswith("run terminal"):
            cmd = re.sub(r'^run (command|terminal)\s*','',lower)
            res = real_files.execute_bash(cmd)
            if res["ok"]: _say(f"Output: {res['stdout'][:300] or '(none)'}", 100, [f"Terminal: {cmd}"])
            else: _error(f"Command failed: {res['stderr'][:200]}")
            return

        # Real calendar
        if any(kw in lower for kw in ["my schedule","today's events","calendar"]):
            info = real_calendar.get_todays_events()
            if info["ok"]:
                if info["events"]: _say(f"{info['count']} events today: " + "; ".join(info["events"]), 100, [info["source"]])
                else: _say("Your calendar is clear today.", 100, [info["source"]])
            else: _error(info["error"])
            return

        # Reminders (real)
        if "my reminders" in lower:
            info = real_calendar.get_reminders()
            if info["ok"]:
                if info["items"]: _say(f"{info['count']} reminders: " + "; ".join(info["items"][:5]), 100, [info["source"]])
                else: _say("No pending reminders.", 100, [info["source"]])
            else: _error(info["error"])
            return

        # System status dashboard
        if "system status" in lower or "what is online" in lower:
            st = ra.get_all()
            on  = [n for n,s in st.items() if s["ok"]]
            off = [n for n,s in st.items() if not s["ok"]]
            msg = f"{len(on)} online: {', '.join(on[:5])}."
            if off: msg += f" {len(off)} offline: {', '.join(off[:4])}."
            _say(msg, 100, ["core.real_access live probe"]); return

        # Clipboard
        if "clipboard" in lower:
            _say(f"Clipboard: {mac.get_clipboard()[:200]}", 100, ["pbpaste (real)"]); return

        # Weather (real API)
        if "weather" in lower:
            honest = ra.honest_response("Weather API","current weather")
            if honest: _error(honest)
            else: _say(internet.get_weather(), 95, ["OpenWeatherMap API"])
            return

        # Screen reading (real OCR)
        if "read my screen" in lower or "what is on my screen" in lower:
            honest = ra.honest_response("Screen Capture","your screen")
            if honest: _error(honest); return
            text = screen_reader.read_screen_text()
            if text:
                res = llm.generate_response(f"Summarise screen: '{text[:800]}'")
                res["sources"] = ["Real Tesseract OCR screenshot"] + res.get("sources",[])
                _say_result(res)
            else: _say("Screenshot taken but no text detected.", 100, ["Tesseract OCR"]); return

        # Memory
        if "remember" in lower and "mode" not in lower:
            if " is " in lower:
                k,_,v = lower.partition(" is ")
                k = k.replace("remember","").strip()
                db.save_fact(k, v.strip())
                _say(f"Saved: {k} = {v.strip()}", 100, ["SQLite memory"])
            elif "remember to" in lower:
                task = lower.replace("remember to","").strip()
                db.add_task(task)
                _say(f"Task added: {task}", 100, ["SQLite memory"])
            return

        if "my tasks" in lower or "task list" in lower:
            tasks = db.get_tasks()
            _say("Tasks: " + "; ".join(tasks) if tasks else "Task list is clear.", 100, ["SQLite memory"]); return

        # Automation modes
        if "mode" in lower and "create" not in lower:
            _say(modes.activate_mode(lower), 100, ["Automation system"]); return

        # Default AI
        _set_state("thinking")
        result = master.process_request(command)
        if isinstance(result, str):
            result = {"reply": result, "confidence": 70, "sources": ["Ollama AI"]}
        _say_result(result)

    except Exception as e:
        logger.error(f"execute_command: {e}", exc_info=True)
        _error(f"Real error occurred: {type(e).__name__}: {str(e)[:100]}. See jarvis_log.txt.")


def jarvis_wake_routine(pre_command=""):
    speaker.play_sound("activate")
    command = pre_command
    if not command:
        _set_state("listening")
        if hud: hud.sig_update_ai.emit("Listening…")
        command = listener.listen_for_command()
    STOP = {"stop","exit","standby","nevermind","that's all","bye","goodbye"}
    while command:
        if any(s in command.lower() for s in STOP):
            _say("Standing by.", 100, ["Session"]); break
        execute_command(command)
        _set_state("listening")
        if hud: hud.sig_update_ai.emit("Listening…")
        command = listener.listen_for_command()
    _set_state("idle")
    if hud: hud.sig_update_ai.emit("Awaiting wake word…")


def _reminder_loop():
    while True:
        try:
            for msg in db.get_due_reminders():
                _say(f"Reminder: {msg}", 100, ["SQLite reminders"])
                mac.send_notification("JARVIS", msg)
        except Exception as e: logger.error(f"reminder: {e}")
        time.sleep(60)


def _briefing_sched():
    fired = False
    while True:
        now = datetime.datetime.now()
        if now.hour == 9 and now.minute == 0 and not fired:
            name = db.get_fact("name") or "Sir"
            tasks = db.get_tasks()
            w = internet.get_weather() if ra.get("Weather API")["ok"] else ""
            msg = f"Good morning {name}. {w} " + (f"Tasks: {', '.join(tasks[:3])}." if tasks else "No tasks today.")
            _say(msg, 90, ["SQLite","OpenWeatherMap"]); fired = True
        elif now.hour != 9: fired = False
        time.sleep(30)


def background_loop():
    db.init_db()
    ra.run_all_probes()
    ra.start_background_polling(5)
    name = db.get_fact("name") or "Sir"
    greeting = f"Welcome back, {name}. JARVIS {JARVIS_VERSION} online. Real-access mode active — no hallucination."
    logger.info(greeting)
    time.sleep(1.2)
    if hud: hud.sig_update_ai.emit(greeting)
    speaker.speak(greeting)
    threading.Thread(target=_reminder_loop, daemon=True).start()
    threading.Thread(target=_briefing_sched, daemon=True).start()
    listener.wait_for_wake_word(jarvis_wake_routine)


def main():
    global hud
    app = QApplication(sys.argv)
    app.setApplicationName(f"JARVIS {JARVIS_VERSION}")
    hud = CinematicHUD()
    hud.show()
    threading.Thread(target=background_loop, daemon=True).start()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
