#!/usr/bin/env python3
"""
krb-cron.py — Headless Kerberos ticket lifecycle manager for cron.

Checks the current default credential cache against a configured list of
principals and takes the appropriate action:
  - No ticket           → kinit -kt for each configured principal
  - Unknown principal   → kdestroy, then kinit -kt for each configured principal
  - Ticket healthy      → log and exit
  - Remaining < renew_threshold AND renew_till still valid → kinit -R (renew)
  - Remaining < renew_threshold AND renew_till expiring    → kinit -kt (new ticket)

Configuration is embedded as a YAML string at the top of this file.
Use --config to supply an external YAML file instead.
"""

import argparse
import getpass
import logging
import platform
import subprocess
import sys
import time

# Note we need two exernal libraries
# - PyYAML for config parsing (pip install pyyaml)
# - krb5 for Kerberos interaction (pip install krb5)
#
# There is a requirements.txt file that should be 
# run with pip to get these dependencies
import yaml
import krb5

# ---------------------------------------------------------------------------
# Embedded default configuration — edit principals and keytab paths here,
# or supply an external file via --config.
#
# Because we are intending to run this from cronn,
# we want to avoid any external files.  This would be a problem
# if someone were to change the configuration and effectively
# allow for an arbitrary principal to be renewed or re-acquired
#
# We stll allow for a config file to be used from the commandline
# so that we can test changes, but for the production version
# it should be run from cron with no arguments
# 
# -AJN
# ---------------------------------------------------------------------------
DEFAULT_CONFIG = """
# These are the settings that control when 
# tickets are renewed vs when new ones are acquired.
settings:
  renew_threshold_hours: 2
  renew_till_threshold_hours: 24      # If less than 1 day remains on the renewal life 
                                      #then we get a new one  
  # log_file: /var/log/krb-cron.log   # optional; uncomment to log to a file

# Note: These are the principals and paths to their keytabs
# That we want to manage with this script.
# If the script finds a ticket that doesn't match one of these
# it will destroy the existing ticket and get new one from this list
principals:
  - name: "mu2edaq/mu2edaq/mu2e.fnal.gov@FNAL.GOV"
    keytab: "/Users/anorman/Kerberos_Keytabs/Mu2e/mu2edaq.keytab"
  - name: "mu2eshift/mu2edaq/mu2e.fnal.gov@FNAL.GOV"
    keytab: "/Users/anorman/Kerberos_Keytabs/Mu2e/mu2eshift.keytab"
  - name: "mu2eraw/mu2edaq/mu2e.fnal.gov@FNAL.GOV"
    keytab: "/Users/anorman/Kerberos_Keytabs/Mu2e/mu2eraw.keytab"
  - name: "mu2edcs/mu2edaq/mu2e.fnal.gov@FNAL.GOV"
    keytab: "/Users/anorman/Kerberos_Keytabs/Mu2e/mu2edcs.keytab"
  - name: "mu2e-teststand/mu2edaq/mu2e.fnal.gov@FNAL.GOV"
    keytab: "/Users/anorman/Kerberos_Keytabs/Mu2e/mu2e-teststand.keytab"
  - name: "mu2e-controlroom/mu2edaq/mu2e.fnal.gov@FNAL.GOV"
    keytab: "/Users/anorman/Kerberos_Keytabs/Mu2e/mu2e-controlroom.keytab"

# Maps the OS username of the logged-in operator to the Kerberos principal
# that should be made active (via kswitch) after tickets are managed.
user_principals:
  mu2edaq: "mu2edaq/mu2edaq/mu2e.fnal.gov@FNAL.GOV"
  mu2eshift: "mu2eshift/mu2edaq/mu2e.fnal.gov@FNAL.GOV"
  mu2eraw: "mu2eraw/mu2edaq/mu2e.fnal.gov@FNAL.GOV"
  anorman: "anorman@FNAL.GOV"
"""

# ---------------------------------------------------------------------------
# Configuration helpers
# ---------------------------------------------------------------------------

def load_config(path=None):
    """Parse embedded YAML default or an external file if path is given.

    Returns a dict with guaranteed keys:
      config["settings"]["renew_threshold_hours"]
      config["settings"]["renew_till_threshold_hours"]
      config["principals"]  — list of {"name": ..., "keytab": ...}
    """
    # Load configuration from external file if provided, otherwise use embedded default
    if path is not None:
        with open(path, "r") as fh:
            data = yaml.safe_load(fh)
    else:
        data = yaml.safe_load(DEFAULT_CONFIG)

    # Ensure the "settings" section exists and populate with defaults if missing
    settings = data.setdefault("settings", {})
    settings.setdefault("renew_threshold_hours", 2)
    settings.setdefault("renew_till_threshold_hours", 24)

    # Validate that at least one principal is configured
    if "principals" not in data or not data["principals"]:
        raise ValueError("Configuration must contain at least one principal entry.")

    data.setdefault("user_principals", {})

    return data


# ---------------------------------------------------------------------------
# Kerberos helpers
# ---------------------------------------------------------------------------

def get_current_principal(ctx, cache):
    """Return the current principal name as a str, or None if no ticket exists."""
    try:
        princ = krb5.cc_get_principal(ctx, cache)
        return princ.name.decode()
    except Exception:
        return None


def get_ticket_times():
    """Parse klist output to return (endtime, renew_till) for the TGT.

    Both values are Unix timestamps (int).  Returns (None, None) on failure.
    Supports MIT Kerberos (Linux) and Heimdal (macOS) date formats.
    """
    import re
    from datetime import datetime

    # MIT Kerberos: "04/20/2026 10:00:00"  /  Heimdal: "Apr 20 10:00:00 2026"
    _dt_pat = (
        r"\d{2}/\d{2}/\d{4} \d{2}:\d{2}:\d{2}"
        r"|[A-Z][a-z]{2} +\d{1,2} \d{2}:\d{2}:\d{2} \d{4}"
    )
    _dt_fmts = ("%m/%d/%Y %H:%M:%S", "%b %d %H:%M:%S %Y")

    def _to_epoch(s):
        for fmt in _dt_fmts:
            try:
                return int(datetime.strptime(s.strip(), fmt).timestamp())
            except ValueError:
                pass
        return None

    try:
        result = subprocess.run(["klist"], capture_output=True, text=True)
        if result.returncode != 0:
            return None, None
    except FileNotFoundError:
        logging.error("klist executable not found")
        return None, None

    endtime = None
    renew_till = None
    for line in result.stdout.splitlines():
        if "krbtgt/" in line:
            dates = re.findall(_dt_pat, line)
            if len(dates) >= 2:
                endtime = _to_epoch(dates[1])  # second column = expires
        elif "renew until" in line.lower():
            dates = re.findall(_dt_pat, line)
            if dates:
                renew_till = _to_epoch(dates[0])

    return endtime, renew_till


# ---------------------------------------------------------------------------
# kinit / kdestroy wrappers
# ---------------------------------------------------------------------------

def _run(cmd, dry_run):
    """Log and optionally execute *cmd* (list of str)."""
    logging.debug("Command: %s", " ".join(cmd))
    # In dry-run mode, only log what would be executed without actually running it
    if dry_run:
        logging.info("[dry-run] would run: %s", " ".join(cmd))
        return
    # Execute the command and handle common failure modes
    try:
        subprocess.run(cmd, check=True)
    except subprocess.CalledProcessError as exc:
        logging.error("Command failed (exit %d): %s", exc.returncode, " ".join(cmd))
    except FileNotFoundError:
        logging.error("Executable not found: %s", cmd[0])


def kinit_new(principal, keytab, dry_run):
    """Obtain a fresh ticket for *principal* using *keytab*."""
    # Build platform-specific kinit command (macOS vs Linux have different flag names)
    os_name = platform.system()
    if os_name == "Darwin":
        # macOS: -f forwardable, -A addressless, -k use keytab, -t keytab path
        cmd = ["kinit", "-f", "-A", "-k", "-t", keytab, principal]
    else:
        # Linux: -5 Kerberos 5, -F forwardable, -A addressless, -k use keytab
        cmd = ["kinit", "-5", "-F", "-A", "-k", "-t", keytab, principal]
    logging.info("Getting new ticket for %s", principal)
    _run(cmd, dry_run)


def kinit_renew(principal, dry_run):
    """Renew the existing ticket for *principal*."""
    # Use kinit -R to renew without requiring password/keytab
    logging.info("Renewing ticket for %s", principal)
    _run(["kinit", "-R", principal], dry_run)


def run_kdestroy(dry_run):
    """Destroy the current default ticket cache."""
    logging.info("Destroying current ticket cache (unknown principal)")
    _run(["kdestroy"], dry_run)


def set_active_principal(user_principals, dry_run):
    """Switch the default credential cache to the principal mapped to the current OS user."""
    username = getpass.getuser()
    principal = user_principals.get(username)
    if principal is None:
        logging.debug("No default principal mapping for user '%s'; skipping kswitch.", username)
        return
    logging.info("Switching active ticket to %s (user: %s)", principal, username)
    _run(["kswitch", "-p", principal], dry_run)


# ---------------------------------------------------------------------------
# Main logic
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(
        description="Headless Kerberos ticket lifecycle manager for cron."
    )
    parser.add_argument(
        "--config",
        metavar="FILE",
        default=None,
        help="Path to a YAML config file (overrides embedded defaults).",
    )
    parser.add_argument(
        "--verbose", "-v",
        action="store_true",
        help="Enable debug-level logging.",
    )
    parser.add_argument(
        "--silent", "-s",
        action="store_true",
        help="Suppress all INFO output; only WARNING and above are shown.",
    )
    parser.add_argument(
        "--dry-run", "-n",
        action="store_true",
        dest="dry_run",
        help="Log intended actions without executing kinit/kdestroy.",
    )
    args = parser.parse_args()

    # --- Logging setup ---
    if args.verbose:
        log_level = logging.DEBUG
    elif args.silent:
        log_level = logging.WARNING
    else:
        log_level = logging.INFO
    log_format = "%(asctime)s %(levelname)s %(message)s"
    logging.basicConfig(format=log_format, level=log_level, stream=sys.stdout)

    # --- Load config ---
    # Load either embedded defaults or external config file with error handling
    try:
        config = load_config(args.config)
    except FileNotFoundError:
        logging.error("Config file not found: %s", args.config)
        sys.exit(1)
    except (yaml.YAMLError, ValueError) as exc:
        logging.error("Invalid config: %s", exc)
        sys.exit(1)

    # Extract configuration values and convert time thresholds to seconds
    settings = config["settings"]
    principals = config["principals"]
    renew_threshold_secs = settings["renew_threshold_hours"] * 3600
    renew_till_threshold_secs = settings["renew_till_threshold_hours"] * 3600

    # Add optional file logging handler if configured
    log_file = settings.get("log_file")
    if log_file:
        fh = logging.FileHandler(log_file)
        fh.setFormatter(logging.Formatter(log_format))
        fh.setLevel(log_level)
        logging.getLogger().addHandler(fh)

    user_principals = config["user_principals"]

    # Build lookup structures for fast principal validation and keytab retrieval
    principal_keytab = {p["name"]: p["keytab"] for p in principals}
    allowed_principals = set(principal_keytab.keys())

    logging.debug(
        "Thresholds: renew<%dh, new-ticket-if-renew_till<%dh",
        settings["renew_threshold_hours"],
        settings["renew_till_threshold_hours"],
    )
    logging.debug("Configured principals: %s", ", ".join(allowed_principals))

    # --- Init krb5 context and default cache ---
    # Initialize the Kerberos library and get handle to the default credential cache
    try:
        ctx = krb5.init_context()
        cache = krb5.cc_default(ctx)
    except Exception as exc:
        logging.error("Failed to initialise krb5 context: %s", exc)
        sys.exit(1)

    # Check what principal (if any) currently holds a ticket
    current_principal = get_current_principal(ctx, cache)

    # --- No ticket: get one for every configured principal ---
    # If there's no active ticket, acquire fresh tickets for all configured principals
    if current_principal is None:
        logging.info("No active Kerberos ticket found.")
        for p in principals:
            kinit_new(p["name"], p["keytab"], args.dry_run)
        set_active_principal(user_principals, args.dry_run)
        sys.exit(0)

    logging.debug("Current principal: %s", current_principal)

    # --- Unknown principal: destroy and re-acquire ---
    # If the existing ticket is for a principal not in our config, destroy it and start fresh
    if current_principal not in allowed_principals:
        logging.warning(
            "Current principal '%s' is not in the allowed list — destroying ticket.",
            current_principal,
        )
        run_kdestroy(args.dry_run)
        for p in principals:
            kinit_new(p["name"], p["keytab"], args.dry_run)
        set_active_principal(user_principals, args.dry_run)
        sys.exit(0)

    # --- Principal is allowed: inspect ticket times ---
    # Get the TGT expiration time and renewable-until time
    endtime, renew_till = get_ticket_times()

    # If we can't read the TGT times, try renewing as a fallback
    if endtime is None:
        logging.warning("Could not read TGT times for %s; attempting renewal.", current_principal)
        kinit_renew(current_principal, args.dry_run)
        set_active_principal(user_principals, args.dry_run)
        sys.exit(0)

    # Calculate how much time remains before expiration and before renew_till
    now = int(time.time())
    remaining = endtime - now
    renew_remaining = (renew_till - now) if renew_till else 0

    logging.debug(
        "Ticket times — remaining: %.1fh, renew_till remaining: %.1fh",
        remaining / 3600,
        renew_remaining / 3600,
    )

    # Look up the keytab path for this principal
    keytab = principal_keytab[current_principal]

    # Decision logic: determine whether to do nothing, renew, or get a new ticket
    if remaining >= renew_threshold_secs:
        # Ticket has plenty of time left — no action needed
        logging.info(
            "Ticket for %s is healthy (%.1fh remaining).",
            current_principal,
            remaining / 3600,
        )
    elif renew_remaining < renew_till_threshold_secs:
        # Ticket is expiring soon AND we can't renew (renew_till is also expiring) — get new ticket
        logging.info(
            "Ticket for %s cannot be renewed (renew_till in %.1fh < %.1fh threshold) — getting new ticket.",
            current_principal,
            renew_remaining / 3600,
            settings["renew_till_threshold_hours"],
        )
        kinit_new(current_principal, keytab, args.dry_run)
    else:
        # Ticket is expiring soon BUT renew_till is still valid — just renew the existing ticket
        logging.info(
            "Ticket for %s has %.1fh remaining (< %.1fh threshold) — renewing.",
            current_principal,
            remaining / 3600,
            settings["renew_threshold_hours"],
        )
        kinit_renew(current_principal, args.dry_run)

    set_active_principal(user_principals, args.dry_run)


if __name__ == "__main__":
    main()
