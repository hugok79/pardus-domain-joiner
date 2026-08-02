#!/usr/bin/python3

import sys
import signal
import os
from pardus_domain_joiner import domain_operations
import psutil

if len(sys.argv) >= 2:
    cmd = sys.argv[1]

    if cmd == "hostname":
        hostname = sys.argv[2].strip()

        domain_operations.config_manager.set_hostname(hostname)

    elif cmd == "join":
        hostname = sys.argv[2].strip()
        domain = sys.argv[3].strip()
        user = sys.argv[4].strip()
        password = sys.stdin.read().strip()
        ouaddress = sys.argv[5].strip()
        connection_type = sys.argv[6].strip()
        workgroup = sys.argv[7].strip()

        error = domain_operations.join(
            hostname,
            domain,
            user,
            password,
            ouaddress=ouaddress,
            realmd=connection_type == "sssd",
            winbind=connection_type == "winbind",
            workgroup=workgroup,
        )

        if error:
            sys.exit(1)
    elif cmd == "leave":
        username = sys.argv[2].strip()
        password = sys.stdin.read().strip()
        is_winbind = True if sys.argv[3].strip() == "winbind" else False

        error = domain_operations.leave(
            user=username,
            password=password,
            winbind=is_winbind,
            realmd=(not is_winbind),
        )

        if error:
            sys.exit(1)
    elif cmd == "check_domain":
        joined_domain_name = domain_operations.list(realmd=True)

        if joined_domain_name:
            print(f"joined={joined_domain_name}")
            exit(0)

        joined_domain_name = domain_operations.list(winbind=True)
        if joined_domain_name:
            print(f"joined={joined_domain_name}")

    elif cmd == "cancel":
        pid = int(sys.argv[2])
        current_uid = os.getuid() # UID of the user executing the command

        try:
            process = psutil.Process(pid)
            process_uid = process.uids().real  # UID of the target process owner

            # Block if the executing user is NOT 'root' AND is NOT the process owner
            if current_uid != 0 and current_uid != process_uid:
                print("Error: You cannot terminate a process belonging to another user!")
                sys.exit(1)

            # Verify if the process belongs to this application
            cmdline = " ".join(process.cmdline())
            if "pardus-domain-joiner" not in cmdline:
                print("The specified PID is not associated with this application!")
                sys.exit(1)

            # Graceful termination
            process.terminate()
            print("Process has been successfully terminated.")

        except psutil.NoSuchProcess:
            print("Specified PID not found.")
        except psutil.AccessDenied:
            print("Access denied for this process.")
