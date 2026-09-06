"""Optional reader for Slack notifications stored by Windows.

Admin.py imports this module only when the file is present.  It does not use a
Slack token, modify notifications or dismiss them.  Removing ReadPush.py is
enough to disable the feature; Admin.py will continue to run normally.
"""

from __future__ import annotations

import asyncio
import importlib
import subprocess
import sys
import threading
from datetime import datetime
from typing import Any


POLL_INTERVAL_SECONDS = 1.0
SLACK_NAME_FRAGMENT = "slack"


def _console_marker() -> str:
    marker = chr(0x1F535)
    try:
        marker.encode(sys.stdout.encoding or "utf-8")
        return marker
    except UnicodeEncodeError:
        # Some older Windows consoles use cp1251. ANSI gives them a cyan dot
        # without allowing an unsupported emoji to stop the listener.
        return "\033[96m●\033[0m" if sys.stdout.isatty() else "[PUSH]"


BLUE_MARKER = _console_marker()

WINRT_PACKAGES = (
    "winrt-Windows.Foundation",
    "winrt-Windows.Foundation.Collections",
    "winrt-Windows.UI.Notifications",
    "winrt-Windows.UI.Notifications.Management",
)


def _load_winrt_types():
    try:
        management = importlib.import_module("winrt.windows.ui.notifications.management")
        notifications = importlib.import_module("winrt.windows.ui.notifications")
    except ImportError:
        print(f"{BLUE_MARKER} Installing Windows notification support...")
        try:
            subprocess.check_call(
                [sys.executable, "-m", "pip", "install", *WINRT_PACKAGES]
            )
        except Exception as error:
            package_list = " ".join(WINRT_PACKAGES)
            raise RuntimeError(
                "cannot install PyWinRT packages. Run: "
                f'"{sys.executable}" -m pip install {package_list}'
            ) from error
        importlib.invalidate_caches()
        management = importlib.import_module("winrt.windows.ui.notifications.management")
        notifications = importlib.import_module("winrt.windows.ui.notifications")

    return (
        management.UserNotificationListener,
        management.UserNotificationListenerAccessStatus,
        notifications.NotificationKinds,
        notifications.KnownNotificationBindings,
    )


def _enum_member(enum_type: Any, name: str) -> Any:
    """Support both the current uppercase and older lowercase PyWinRT enums."""
    for candidate in (name, name.lower()):
        if hasattr(enum_type, candidate):
            return getattr(enum_type, candidate)
    raise AttributeError(f"{enum_type.__name__}.{name} is unavailable")


def _app_name(notification: Any) -> str:
    try:
        return str(notification.app_info.display_info.display_name).strip()
    except Exception:
        return ""


def _text_fields(notification: Any, toast_generic: Any) -> list[str]:
    try:
        binding = notification.notification.visual.get_binding(toast_generic)
        if binding is None:
            return []
        return [
            str(element.text).strip()
            for element in binding.get_text_elements()
            if str(element.text).strip()
        ]
    except Exception:
        return []


def _creation_time(notification: Any) -> str:
    try:
        value = notification.creation_time
        if isinstance(value, datetime):
            return value.astimezone().strftime("%d.%m.%Y %H:%M:%S")
        return str(value)
    except Exception:
        return "unknown"


def _notification_key(notification: Any, app_name: str) -> tuple[str, int, str]:
    return (app_name.casefold(), int(notification.id), _creation_time(notification))


def _print_slack_notification(notification: Any, app_name: str, toast_generic: Any) -> None:
    texts = _text_fields(notification, toast_generic)
    sender = texts[0] if texts else "not available"
    message = " | ".join(texts[1:]) if len(texts) > 1 else "not available"
    print()
    print(f"{BLUE_MARKER} SLACK PUSH")
    print(f"  App: {app_name or 'Slack'}")
    print(f"  Sender/title: {sender}")
    print(f"  Message: {message}")
    print(f"  Time: {_creation_time(notification)}")
    print(f"  Windows notification ID: {notification.id}")
    print("> ", end="", flush=True)


async def _request_access(listener: Any, allowed_status: Any) -> bool:
    try:
        status = listener.get_access_status()
        if status == allowed_status:
            return True
        status = await listener.request_access_async()
        if status == allowed_status:
            return True
        print(
            f"{BLUE_MARKER} Slack push listener has no Windows permission "
            f"(status: {status})."
        )
        return False
    except Exception as error:
        print(
            f"{BLUE_MARKER} Slack push listener cannot request Windows access: {error}. "
            "This Windows configuration may block notification access for an "
            "unpackaged Python program."
        )
        return False


async def _listen(stop_event: threading.Event) -> None:
    (
        UserNotificationListener,
        UserNotificationListenerAccessStatus,
        NotificationKinds,
        KnownNotificationBindings,
    ) = _load_winrt_types()

    listener = UserNotificationListener.current
    allowed = _enum_member(UserNotificationListenerAccessStatus, "ALLOWED")
    toast = _enum_member(NotificationKinds, "TOAST")
    toast_generic = _enum_member(KnownNotificationBindings, "TOAST_GENERIC")
    if not await _request_access(listener, allowed):
        return

    # Build a baseline so old entries still present in Action Center are not
    # printed as if they arrived after Admin started.
    initial = await listener.get_notifications_async(toast)
    seen = {
        _notification_key(item, _app_name(item))
        for item in initial
        if SLACK_NAME_FRAGMENT in _app_name(item).casefold()
    }
    print(
        f"{BLUE_MARKER} Slack push listener started "
        f"({len(seen)} existing notification(s) ignored)"
    )

    consecutive_errors = 0
    while not stop_event.is_set():
        try:
            current = await listener.get_notifications_async(toast)
            for notification in current:
                app_name = _app_name(notification)
                if SLACK_NAME_FRAGMENT not in app_name.casefold():
                    continue
                key = _notification_key(notification, app_name)
                if key in seen:
                    continue
                seen.add(key)
                _print_slack_notification(notification, app_name, toast_generic)

            # Prevent an indefinitely growing set while retaining enough history
            # to avoid duplicates when Action Center is opened or refreshed.
            if len(seen) > 5000:
                live_keys = {
                    _notification_key(item, _app_name(item))
                    for item in current
                    if SLACK_NAME_FRAGMENT in _app_name(item).casefold()
                }
                seen = live_keys
            consecutive_errors = 0
        except Exception as error:
            consecutive_errors += 1
            print(
                f"{BLUE_MARKER} Slack push read error: {error} "
                f"(attempt {consecutive_errors}/3)"
            )
            if consecutive_errors >= 3:
                print(
                    f"{BLUE_MARKER} Slack push listener disabled after repeated "
                    "Windows API errors; the rest of Admin remains active"
                )
                return
            await asyncio.sleep(5)
            continue
        await asyncio.sleep(POLL_INTERVAL_SECONDS)


def _thread_main(stop_event: threading.Event) -> None:
    try:
        asyncio.run(_listen(stop_event))
    except Exception as error:
        print(f"{BLUE_MARKER} Slack push listener stopped: {error}")


def start_slack_notification_listener(
    stop_event: threading.Event,
) -> threading.Thread | None:
    """Start listening in a daemon thread and return that thread."""
    # Microsoft requires the permission request on the caller's UI/main thread.
    # Admin invokes this function from its main console thread before input starts.
    (
        UserNotificationListener,
        UserNotificationListenerAccessStatus,
        _NotificationKinds,
        _KnownNotificationBindings,
    ) = _load_winrt_types()
    listener = UserNotificationListener.current
    allowed = _enum_member(UserNotificationListenerAccessStatus, "ALLOWED")
    if not asyncio.run(_request_access(listener, allowed)):
        return None

    thread = threading.Thread(
        target=_thread_main,
        args=(stop_event,),
        name="Slack push listener",
        daemon=True,
    )
    thread.start()
    return thread


if __name__ == "__main__":
    standalone_stop = threading.Event()
    print(f"{BLUE_MARKER} Press Ctrl+C to stop")
    worker = start_slack_notification_listener(standalone_stop)
    if worker is None:
        raise SystemExit(1)
    try:
        while worker.is_alive():
            worker.join(timeout=0.5)
    except KeyboardInterrupt:
        standalone_stop.set()
        worker.join(timeout=3)
