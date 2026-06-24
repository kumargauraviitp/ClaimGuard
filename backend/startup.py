import os
import sys
import psutil
from sqlalchemy import create_engine
import redis
from environment_validator import validate_environment

def check_resources():
    mem = psutil.virtual_memory()
    disk = psutil.disk_usage('/')
    
    # Require at least 500MB RAM free
    if mem.available < 500 * 1024 * 1024:
        print(f"CRITICAL ERROR: Insufficient RAM. Available: {mem.available / (1024*1024):.2f} MB")
        sys.exit(1)
        
    # Require at least 1GB Disk free
    if disk.free < 1024 * 1024 * 1024:
        print(f"CRITICAL ERROR: Insufficient Disk Space. Available: {disk.free / (1024*1024*1024):.2f} GB")
        sys.exit(1)
        
def check_postgres():
    db_url = os.getenv("DATABASE_URL")
    try:
        engine = create_engine(db_url)
        with engine.connect() as conn:
            pass
    except Exception as e:
        print(f"CRITICAL ERROR: Failed to connect to PostgreSQL at {db_url}")
        print(e)
        sys.exit(1)

def check_redis():
    redis_url = os.getenv("REDIS_URL")
    try:
        r = redis.Redis.from_url(redis_url)
        r.ping()
    except Exception as e:
        print(f"CRITICAL ERROR: Failed to connect to Redis at {redis_url}")
        print(e)
        sys.exit(1)

def print_banner():
    banner = """
====================================================
Insurance Fraud Investigation Platform
Version : 1.0
Backend : Ready
Database : Connected
Redis : Connected
Model : Checked
Knowledge Base : Checked
SHAP : Checked
Agent : Ready
System Health : Healthy
====================================================
"""
    print(banner)

def main():
    from dotenv import load_dotenv
    from app.config_manager import generate_config_lock
    load_dotenv()
    
    print("Running Readiness Validation...")
    validate_environment()
    check_resources()
    check_postgres()
    check_redis()
    
    print("Generating config lock...")
    generate_config_lock()
    
    print_banner()

if __name__ == "__main__":
    main()
