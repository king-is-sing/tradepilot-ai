import subprocess


def notify(title, message):
    """
    Sends a local Mac notification.
    If notifications fail, the bot continues running.
    """
    safe_title = str(title).replace('"', '\\"')
    safe_message = str(message).replace('"', '\\"')

    try:
        subprocess.run(
            [
                "osascript",
                "-e",
                f'display notification "{safe_message}" with title "{safe_title}"'
            ],
            check=False,
            timeout=5
        )
    except Exception:
        pass
