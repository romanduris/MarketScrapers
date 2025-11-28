import subprocess
import sys

def run(cmd):
    """Spustí príkaz a vypíše výstup, ukončí pri chybe."""
    try:
        result = subprocess.run(cmd, check=True, capture_output=True, text=True)
        print(result.stdout)
    except subprocess.CalledProcessError as e:
        print(f"❌ Chyba pri spustení: {' '.join(cmd)}")
        print(e.stderr)
        sys.exit(1)

def main():
    print("📦 Adding all changes...")
    run(["git", "add", "."])

    print("📝 Committing...")
    run(["git", "commit", "-m", "Update Container", "--allow-empty"])

    print("🚀 Pushing to origin main...")
    run(["git", "push", "origin", "main"])

    print("✅ Hotovo!")

if __name__ == "__main__":
    main()
