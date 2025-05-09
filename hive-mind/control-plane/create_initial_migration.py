#!/usr/bin/env python3
"""
Script to generate the initial Alembic migration for the database

Run this script to:
1. Create the migrations directory if it doesn't exist
2. Initialize Alembic if not already initialized
3. Generate the initial migration
"""

import os
import subprocess
import sys
from pathlib import Path


def create_migration():
    """
    Create the initial Alembic migration
    """
    # Ensure we're in the control-plane directory
    control_plane_dir = Path(__file__).parent

    # Create migrations directory if it doesn't exist
    migrations_dir = control_plane_dir / "migrations"
    versions_dir = migrations_dir / "versions"
    
    if not migrations_dir.exists():
        print("Creating migrations directory...")
        migrations_dir.mkdir(exist_ok=True)
    
    # Check if versions directory exists
    if not versions_dir.exists():
        # Initialize Alembic
        print("Initializing Alembic...")
        subprocess.run(["alembic", "init", "migrations"], cwd=control_plane_dir, check=True)
    
    # Generate initial migration
    print("Generating initial migration...")
    subprocess.run(
        ["alembic", "revision", "--autogenerate", "-m", "initial"], 
        cwd=control_plane_dir, 
        check=True
    )
    
    print(
        "\nInitial migration created successfully!\n"
        "To apply the migration, run:\n"
        "alembic upgrade head"
    )


if __name__ == "__main__":
    try:
        create_migration()
    except subprocess.CalledProcessError as e:
        print(f"Error running Alembic command: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1) 