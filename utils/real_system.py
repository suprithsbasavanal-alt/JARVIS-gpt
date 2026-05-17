"""
utils/real_system.py  —  JARVIS 3.0 REAL SYSTEM ACCESS
Returns live psutil data — actual values, not estimates.
Every function documents its data source so JARVIS can cite it.
"""

import subprocess
import logging
import platform
from datetime import datetime

import psutil

logger = logging.getLogger("JARVIS.real_system")

SOURCE = "psutil (live kernel data)"   # citation label for all responses


def cpu_info() -> dict:
    """
    Returns REAL CPU data per core using psutil.
    Source: macOS kernel via psutil.
    """
    try:
        per_core     = psutil.cpu_percent(interval=0.5, percpu=True)
        total        = psutil.cpu_percent(interval=0)
        freq         = psutil.cpu_freq()
        logical_cnt  = psutil.cpu_count(logical=True)
        physical_cnt = psutil.cpu_count(logical=False)
        return {
            "ok"           : True,
            "total_percent": total,
            "per_core"     : per_core,
            "logical_cores": logical_cnt,
            "physical_cores": physical_cnt,
            "freq_mhz"     : round(freq.current, 0) if freq else None,
            "source"       : SOURCE,
        }
    except Exception as e:
        logger.error(f"cpu_info error: {e}")
        return {"ok": False, "error": str(e), "source": SOURCE}


def ram_info() -> dict:
    """Returns REAL RAM usage. Source: psutil virtual_memory()"""
    try:
        vm = psutil.virtual_memory()
        return {
            "ok"            : True,
            "total_gb"      : round(vm.total / 1e9, 2),
            "used_gb"       : round(vm.used  / 1e9, 2),
            "available_gb"  : round(vm.available / 1e9, 2),
            "percent"       : vm.percent,
            "source"        : SOURCE,
        }
    except Exception as e:
        return {"ok": False, "error": str(e), "source": SOURCE}


def disk_info() -> list[dict]:
    """Returns REAL disk usage for all mounted partitions. Source: psutil."""
    results = []
    try:
        for part in psutil.disk_partitions():
            try:
                usage = psutil.disk_usage(part.mountpoint)
                results.append({
                    "mountpoint" : part.mountpoint,
                    "device"     : part.device,
                    "fstype"     : part.fstype,
                    "total_gb"   : round(usage.total / 1e9, 2),
                    "used_gb"    : round(usage.used  / 1e9, 2),
                    "free_gb"    : round(usage.free  / 1e9, 2),
                    "percent"    : usage.percent,
                    "source"     : SOURCE,
                })
            except PermissionError:
                pass
    except Exception as e:
        logger.error(f"disk_info error: {e}")
    return results


def battery_info() -> dict:
    """Returns REAL battery status. Source: psutil."""
    try:
        bat = psutil.sensors_battery()
        if bat:
            secs_left = bat.secsleft
            time_left = f"{secs_left // 3600}h {(secs_left % 3600) // 60}m" if secs_left > 0 else "Calculating..."
            return {
                "ok"         : True,
                "percent"    : round(bat.percent, 1),
                "plugged_in" : bat.power_plugged,
                "time_left"  : time_left,
                "source"     : SOURCE,
            }
        return {"ok": False, "error": "No battery found (desktop Mac?)", "source": SOURCE}
    except Exception as e:
        return {"ok": False, "error": str(e), "source": SOURCE}


def network_info() -> dict:
    """Returns REAL network I/O counters. Source: psutil."""
    try:
        net = psutil.net_io_counters()
        return {
            "ok"        : True,
            "sent_mb"   : round(net.bytes_sent  / 1e6, 2),
            "recv_mb"   : round(net.bytes_recv  / 1e6, 2),
            "packets_sent": net.packets_sent,
            "packets_recv": net.packets_recv,
            "source"    : SOURCE,
        }
    except Exception as e:
        return {"ok": False, "error": str(e), "source": SOURCE}


def top_processes(n: int = 10) -> list[dict]:
    """
    Returns the top N processes by CPU usage RIGHT NOW.
    Source: psutil process iterator.
    """
    procs = []
    try:
        for proc in psutil.process_iter(["pid", "name", "cpu_percent", "memory_percent"]):
            try:
                info = proc.info
                procs.append(info)
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                pass
        procs.sort(key=lambda p: p.get("cpu_percent", 0), reverse=True)
        return procs[:n]
    except Exception as e:
        logger.error(f"top_processes error: {e}")
        return []


def mac_model() -> dict:
    """
    Returns real Mac model info using system_profiler.
    Source: macOS system_profiler SPHardwareDataType.
    """
    try:
        result = subprocess.run(
            ["system_profiler", "SPHardwareDataType"],
            capture_output=True, text=True, timeout=10
        )
        lines   = result.stdout.strip().split("\n")
        info    = {}
        for line in lines:
            if ":" in line:
                key, _, val = line.partition(":")
                info[key.strip()] = val.strip()
        return {"ok": True, "data": info, "source": "system_profiler SPHardwareDataType"}
    except Exception as e:
        return {"ok": False, "error": str(e), "source": "system_profiler"}


def macos_version() -> str:
    """Returns real macOS version string."""
    return platform.mac_ver()[0] or platform.version()


def get_ip_address() -> dict:
    """Returns real local IP address. Source: ifconfig / socket."""
    try:
        result = subprocess.run(
            ["ipconfig", "getifaddr", "en0"],
            capture_output=True, text=True, timeout=5
        )
        ip = result.stdout.strip()
        if ip:
            return {"ok": True, "ip": ip, "interface": "en0", "source": "ipconfig"}
        # Fallback: en1 (Ethernet)
        result2 = subprocess.run(
            ["ipconfig", "getifaddr", "en1"],
            capture_output=True, text=True, timeout=5
        )
        ip2 = result2.stdout.strip()
        return {"ok": bool(ip2), "ip": ip2 or "Not found", "interface": "en1", "source": "ipconfig"}
    except Exception as e:
        return {"ok": False, "ip": "Unknown", "error": str(e), "source": "ipconfig"}


def full_stats_summary() -> str:
    """
    Returns a complete, real, human-readable system status string.
    Every number comes from live psutil / system_profiler data.
    """
    cpu  = cpu_info()
    ram  = ram_info()
    bat  = battery_info()
    net  = network_info()
    disks = disk_info()

    lines = [f"[Source: {SOURCE} — live data at {datetime.now().strftime('%H:%M:%S')}]"]

    if cpu["ok"]:
        lines.append(f"CPU: {cpu['total_percent']}% total | {cpu['logical_cores']} cores")
    else:
        lines.append(f"CPU: Error — {cpu['error']}")

    if ram["ok"]:
        lines.append(f"RAM: {ram['percent']}% — {ram['used_gb']}GB used of {ram['total_gb']}GB")
    else:
        lines.append(f"RAM: Error — {ram['error']}")

    if bat["ok"]:
        plug = "charging" if bat["plugged_in"] else f"on battery, {bat['time_left']} remaining"
        lines.append(f"Battery: {bat['percent']}% ({plug})")
    else:
        lines.append(f"Battery: {bat.get('error', 'N/A')}")

    if net["ok"]:
        lines.append(f"Network: ↑{net['sent_mb']} MB sent | ↓{net['recv_mb']} MB received")

    for d in disks:
        if d["mountpoint"] == "/":
            lines.append(f"Disk (/): {d['percent']}% used — {d['free_gb']}GB free of {d['total_gb']}GB")

    return "\n".join(lines)
