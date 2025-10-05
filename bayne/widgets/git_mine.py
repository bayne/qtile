import os
import subprocess

from libqtile import log_utils
from libqtile import widget

logger = log_utils.logger

class GitMineStatus(widget.base.ThreadPoolText):
    defaults = [
        ("update_interval", 30, "Update time in seconds."),
        ("foreground", "ffffff", "foreground color"),
    ]

    def __init__(self, **config):
        widget.base.ThreadPoolText.__init__(self, "", **config)
        self.add_defaults(GitMineStatus.defaults)

    def _check_1password_processes(self):
        """Look for 1Password-related processes."""
        try:
            result = subprocess.run(['ps', 'aux'], check=True, stdout=subprocess.PIPE)
            processes = result.stdout.decode().splitlines()
            onepassword_processes = [proc for proc in processes if '1password' in proc.lower()]

            return bool(onepassword_processes)
        except subprocess.CalledProcessError as e:
            logger.exception("Error checking processes {}", e.stderr.decode.strip())
            return False

    def _poll(self):

        # Define repository status counts
        behind_count = 0
        ahead_count = 0
        conflict_count = 0
        up_to_date_count = 0
        pending_count = 0

        base_dir = os.path.expanduser("~/Code/mine")

        for item in os.listdir(base_dir):
            item_path = os.path.join(base_dir, item)
            if not os.path.isdir(item_path):
                continue
            if ".git" in os.listdir(item_path):
                try:
                    repo_dir = item_path
                    if self._check_1password_processes():
                        subprocess.run(
                            ["git", "-C", repo_dir, "fetch"],
                            stdout=subprocess.DEVNULL,
                            stderr=subprocess.DEVNULL
                        )
                    else:
                        logger.warning("Skipping git fetch for 1Password repo")
                    status_output = subprocess.check_output(
                        ["git", "-C", repo_dir, "status", "--porcelain",
                         "--branch"],
                        stderr=subprocess.DEVNULL
                        ).decode()

                    if len(status_output.splitlines()) > 1:
                        pending_count += 1
                    elif "##" in status_output:
                        if ("[ahead" in status_output and "[behind" in
                            status_output):
                            conflict_count += 1
                        elif "[ahead" in status_output:
                            ahead_count += 1
                        elif "[behind" in status_output:
                            behind_count += 1
                        else:
                            up_to_date_count += 1
                except Exception as e:
                    logger.exception(f"Error processing git repository at {repo_dir}")
        return (f"<b>(↩️{behind_count})(⬆️{ahead_count})(✖️{conflict_count})("
                f"✔️{up_to_date_count})(⋮{pending_count})</b>")

    def poll(self):
        try:
            return self._poll()
        except Exception as e:
            logger.exception("Failed to poll for git status")
            return f"Error something went wrong"

