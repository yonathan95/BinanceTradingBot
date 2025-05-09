#!/usr/bin/env python3
"""
Database setup and initialization script

This script will:
1. Create the database if it doesn't exist
2. Create a migrations directory if it doesn't exist
3. Generate the initial migration
4. Apply the migration to create all tables
5. Seed the database with initial data

Usage:
    python setup_db.py

"""

import os
import subprocess
import sys
import asyncio
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Define control plane directory
control_plane_dir = Path(__file__).parent


def run_command(command, cwd=control_plane_dir):
    """Run a command and print its output"""
    print(f"Running: {' '.join(command)}")
    result = subprocess.run(command, cwd=cwd, check=True, text=True, capture_output=True)
    if result.stdout:
        print(result.stdout)
    if result.stderr:
        print(result.stderr, file=sys.stderr)
    return result


async def setup_database():
    """Setup and initialize the database"""
    try:
        # 1. Create migrations directory and initialize Alembic if needed
        migrations_dir = control_plane_dir / "migrations"
        versions_dir = migrations_dir / "versions"
        
        if not migrations_dir.exists():
            print("Creating migrations directory...")
            migrations_dir.mkdir(exist_ok=True)
        
        # Check if Alembic is initialized
        if not (migrations_dir / "env.py").exists():
            print("Initializing Alembic...")
            run_command(["alembic", "init", "migrations"])
            
            # Copy our custom env.py and script.py.mako
            if (control_plane_dir / "migrations/env.py.template").exists():
                run_command(["cp", "migrations/env.py.template", "migrations/env.py"])
            
            if (control_plane_dir / "migrations/script.py.mako.template").exists():
                run_command(["cp", "migrations/script.py.mako.template", "migrations/script.py.mako"])
        
        # 2. Create versions directory if it doesn't exist
        if not versions_dir.exists():
            print("Creating versions directory...")
            versions_dir.mkdir(exist_ok=True)
        
        # 3. Generate initial migration if no migrations exist
        migration_files = list(versions_dir.glob("*.py"))
        if not migration_files:
            print("Generating initial migration...")
            run_command(["alembic", "revision", "--autogenerate", "-m", "initial"])
        else:
            print(f"Found {len(migration_files)} existing migrations, skipping generation.")
        
        # 4. Apply migrations
        print("Applying migrations...")
        run_command(["alembic", "upgrade", "head"])
        
        # 5. Seed the database with initial data
        print("Seeding database with initial data...")
        # Run the init_db.py script
        from init_db import init_db
        await init_db()
        
        print("\nDatabase setup complete!")
        
    except subprocess.CalledProcessError as e:
        print(f"Error running command: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(setup_database()) 