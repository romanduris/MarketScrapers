"""
Jednoduchá pipeline: spustí všetky kroky projektu po sebe ako samostatné skripty.
Pred spustením overí každý modul z requirements.txt a ak chýba, nainštaluje ho a vypíše progress.
"""

import subprocess
import sys
from pathlib import Path

# Zoznam skriptov podľa poradia
pipeline_steps = [
    "step1_Sraper.py",
    "step2_techAnalyze.py",
    "step3_sentiment.py",
    "step4_ranking.py",
    "step5_AI_comment.py",
    "step6_report_html.py",
    "step7_send_report.py"
]

def check_and_install_module(module_name):
    """Overí, či je modul nainštalovaný, ak nie, nainštaluje ho."""
    try:
        __import__(module_name)
        print(f"✅ Modul '{module_name}' je už nainštalovaný.")
    except ImportError:
        print(f"📦 Modul '{module_name}' nie je nainštalovaný, inštalujem...")
        result = subprocess.run([sys.executable, "-m", "pip", "install", module_name], capture_output=True, text=True)
        if result.returncode == 0:
            print(f"✅ Modul '{module_name}' úspešne nainštalovaný.")
        else:
            print(f"❌ Chyba pri inštalácii modulu '{module_name}':")
            print(result.stderr)

def install_requirements():
    """Prečíta requirements.txt a postupne overí a nainštaluje každý modul."""
    req_file = Path("requirements.txt")
    if not req_file.exists():
        print("⚠️ Súbor requirements.txt neexistuje, preskakujem inštaláciu modulov.")
        return

    print("📦 Overujem a inštalujem moduly z requirements.txt...")
    with open(req_file, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            # Pre moduly s verziou rozdelíme na meno a verziu
            module_name = line.split("==")[0]
            check_and_install_module(module_name)

def run_pipeline():
    print("🚀 Spúšťam jednoduchú pipeline...\n")

    # Krok 0: overiť a nainštalovať requirements
    install_requirements()
    
    # Spustenie jednotlivých skriptov
    for i, step in enumerate(pipeline_steps, start=1):
        print(f"\n--- Krok {i}: Spúšťam {step} ---")
        result = subprocess.run([sys.executable, step])
        if result.returncode != 0:
            print(f"❌ Krok {step} skončil s chybou ({result.returncode}). Pipeline sa zastavuje.")
            break
    else:
        print("\n🎯 Pipeline úspešne dokončená!")

if __name__ == "__main__":
    run_pipeline()
