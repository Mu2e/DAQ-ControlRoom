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
import logging
import platform
import subprocess
import sys
import time

import yaml
import krb5

# ---------------------------------------------------------------------------
# Embedded default configuration — edit principals and keytab paths here,
# or supply an external file via --config.
# ---------------------------------------------------------------------------
DEFAULT_CONFIG = """
settings:
  renew_threshold_hours: 2
  renew_till_threshold_hours: 24
  # log_file: /var/log/krb-cron.log   # optional; uncomment to log to a file

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
    if path is not None:
        with open(path, "r") as fh:
            data = yaml.safe_load(fh)
    else:
        data = yaml.safe_load(DEFAULT_CONFIG)

    settings = data.setdefault("settings", {})
    settings.setdefault("renew_threshold_hours", 2)
    settings.setdefault("renew_till_threshold_hours", 24)

    if "principals" not in data or not data["principals"]:
        raise ValueError("Configuration must contain at least one principal entry.")

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


def get_ticket_times(ctx, cache):
    """Iterate credentials in *cache* and return (endtime, renew_till) for the TGT.

    Both values are Unix timestamps (int).  Returns (None, None) if no TGT is found.
    """
    cursor = krb5.cc_start_seq_get(ctx, cache)
    endtime = None
    renew_till = None
    try:
        while True:
            try:
                cred = krb5.cc_next_cred(ctx, cache, cursor)
                server_name = cred.server.name
                # server_name may be bytes or str depending on library version
                if isinstance(server_name, bytes):
                    server_name = server_name.decode()
                if "krbtgt/" in server_name:
                    endtime = cred.times.endtime
                    renew_till = cred.times.renew_till
                    break
            except krb5.Krb5Error:
                break
    finally:
        try:
            krb5.cc_end_seq_get(ctx, cache, cursor)
        except Exception:
            pass
    return endtime, renew_till


# ---------------------------------------------------------------------------
# kinit / kdestroy wrappers
# ---------------------------------------------------------------------------

def _run(cmd, dry_run):
    """Log and optionally execute *cmd* (list of str)."""
    logging.debug("Command: %s", " ".join(cmd))
    if dry_run:
        logging.info("[dry-run] would run: %s", " ".join(cmd))
        return
    try:
        subprocess.run(cmd, check=True)
    except subprocess.CalledProcessError as exc:
        logging.error("Command failed (exit %d): %s", exc.returncode, " ".join(cmd))
    except FileNotFoundError:
        logging.error("Executable not found: %s", cmd[0])


def kinit_new(principal, keytab, dry_run):
    """Obtain a fresh ticket for *principal* using *keytab*."""
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
    logging.info("Renewing ticket for %s", principal)
    _run(["kinit", "-R", principal], dry_run)


def run_kdestroy(dry_run):
    """Destroy the current default ticket cache."""
    logging.info("Destroying current ticket cache (unknown principal)")
    _run(["kdestroy"], dry_run)


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
        "--dry-run", "-n",
        action="store_true",
        dest="dry_run",
        help="Log intended actions without executing kinit/kdestroy.",
    )
    args = parser.parse_args()

    # --- Logging setup ---
    log_level = logging.DEBUG if args.verbose else logging.INFO
    log_format = "%(asctime)s %(levelname)s %(message)s"
    logging.basicConfig(format=log_format, level=log_level, stream=sys.stdout)

    # --- Load config ---
    try:
        config = load_config(args.config)
    except FileNotFoundError:
        logging.error("Config file not found: %s", args.config)
        sys.exit(1)
    except (yaml.YAMLError, ValueError) as exc:
        logging.error("Invalid config: %s", exc)
        sys.exit(1)

    settings = config["settings"]
    principals = config["principals"]
    renew_threshold_secs = settings["renew_threshold_hours"] * 3600
    renew_till_threshold_secs = settings["renew_till_threshold_hours"] * 3600

    # Optional file handler
    log_file = settings.get("log_file")
    if log_file:
        fh = logging.FileHandler(log_file)
        fh.setFormatter(logging.Formatter(log_format))
        fh.setLevel(log_level)
        logging.getLogger().addHandler(fh)

    # Build lookup: principal name → keytab path
    principal_keytab = {p["name"]: p["keytab"] for p in principals}
    allowed_principals = set(principal_keytab.keys())

    logging.debug(
        "Thresholds: renew<%dh, new-ticket-if-renew_till<%dh",
        settings["renew_threshold_hours"],
        settings["renew_till_threshold_hours"],
    )
    logging.debug("Configured principals: %s", ", ".join(allowed_principals))

    # --- Init krb5 context and default cache ---
    try:
        ctx = krb5.init_context()
        cache = krb5.cc_default(ctx)
    except Exception as exc:
        logging.error("Failed to initialise krb5 context: %s", exc)
        sys.exit(1)

    current_principal = get_current_principal(ctx, cache)

    # --- No ticket: get one for every configured principal ---
    if current_principal is None:
        logging.info("No active Kerberos ticket found.")
        for p in principals:
            kinit_new(p["name"], p["keytab"], args.dry_run)
        sys.exit(0)

    logging.debug("Current principal: %s", current_principal)

    # --- Unknown principal: destroy and re-acquire ---
    if current_principal not in allowed_principals:
        logging.warning(
            "Current principal '%s' is not in the allowed list — destroying ticket.",
            current_principal,
        )
        run_kdestroy(args.dry_run)
        for p in principals:
            kinit_new(p["name"], p["keytab"], args.dry_run)
        sys.exit(0)

    # --- Principal is allowed: inspect ticket times ---
    endtime, renew_till = get_ticket_times(ctx, cache)

    if endtime is None:
        logging.warning("Could not read TGT times for %s; attempting renewal.", current_principal)
        kinit_renew(current_principal, args.dry_run)
        sys.exit(0)

    now = int(time.time())
    remaining = endtime - now
    renew_remaining = (renew_till - now) if renew_till else 0

    logging.debug(
        "Ticket times — remaining: %.1fh, renew_till remaining: %.1fh",
        remaining / 3600,
        renew_remaining / 3600,
    )

    keytab = principal_keytab[current_principal]

    if remaining >= renew_threshold_secs:
        logging.info(
            "Ticket for %s is healthy (%.1fh remaining).",
            current_principal,
            remaining / 3600,
        )
    elif renew_remaining < renew_till_threshold_secs:
        logging.info(
            "Ticket for %s cannot be renewed (renew_till in %.1fh < %.1fh threshold) — getting new ticket.",
            current_principal,
            renew_remaining / 3600,
            settings["renew_till_threshold_hours"],
        )
        kinit_new(current_principal, keytab, args.dry_run)
    else:
        logging.info(
            "Ticket for %s has %.1fh remaining (< %.1fh threshold) — renewing.",
            current_principal,
            remaining / 3600,
            settings["renew_threshold_hours"],
        )
        kinit_renew(current_principal, args.dry_run)


if __name__ == "__main__":
    main()
