"""
Script to create and apply an initial database migration.
"""
import os
import sys
import subprocess


def run_command(command):
    """Run a shell command and print the output."""
    print(f"Running: {command}")
    result = subprocess.run(command, shell=True, capture_output=True, text=True)
    
    if result.stdout:
        print(result.stdout)
    
    if result.stderr:
        print(f"Error: {result.stderr}", file=sys.stderr)
    
    return result.returncode


def main():
    """Create and apply the initial migration."""
    # Create the directory if it doesn't exist
    os.makedirs("alembic/versions", exist_ok=True)
    
    # Create an initial migration
    print("Creating initial migration...")
    result = run_command("alembic revision --autogenerate -m \"Initial database schema\"")
    
    if result != 0:
        print("Failed to create migration.")
        return result
    
    # Apply the migration
    print("\nApplying migration...")
    result = run_command("alembic upgrade head")
    
    if result != 0:
        print("Failed to apply migration.")
        return result
    
    print("\nDatabase migration completed successfully!")
    return 0


if __name__ == "__main__":
    sys.exit(main())
