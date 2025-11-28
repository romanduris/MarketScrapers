import subprocess

def git_update_main():
    try:
        # Prepnúť na main
        subprocess.run(["git", "checkout", "main"], check=True)
        
        # Stiahnuť najnovšie zmeny
        result = subprocess.run(
            ["git", "pull", "origin", "main"], 
            check=True, 
            capture_output=True, text=True
        )
        
        print("✅ Git pull output:\n", result.stdout)
    except subprocess.CalledProcessError as e:
        print("❌ Chyba pri git operácii:")
        print(e.stderr)

if __name__ == "__main__":
    git_update_main()
