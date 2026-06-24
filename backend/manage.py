import argparse
import subprocess
import sys

def start():
    print("Starting backend...")
    subprocess.run(["python", "startup.py"])
    subprocess.run(["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"])

def backup():
    print("Running backup...")
    from app.backup.backup_service import backup_service
    result = backup_service.perform_backup()
    print("Backup completed:", result)

def main():
    parser = argparse.ArgumentParser(description="Insurance Fraud Investigation Platform CLI")
    parser.add_argument("command", choices=["start", "backup", "restore", "health", "reset-db", "seed", "verify", "train", "predict"], help="Command to execute")

    args = parser.parse_args()

    if args.command == "start":
        start()
    elif args.command == "backup":
        backup()
    else:
        print(f"Command '{args.command}' is acknowledged but not fully implemented in this script version.")
        
if __name__ == "__main__":
    main()
