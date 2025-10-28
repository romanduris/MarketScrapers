"""
Jednoduchá pipeline: spustí všetky kroky projektu po sebe ako samostatné skripty.
Nie je potrebné importovať funkcie.
"""

import subprocess

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

def run_pipeline():
    print("🚀 Spúšťam jednoduchú pipeline...\n")
    for i, step in enumerate(pipeline_steps, start=1):
        print(f"--- Krok {i}: Spúšťam {step} ---")
        result = subprocess.run(["python", step])
        if result.returncode != 0:
            print(f"❌ Krok {step} skončil s chybou. Pipeline sa zastavuje.")
            break
    else:
        print("\n🎯 Pipeline úspešne dokončená!")

if __name__ == "__main__":
    run_pipeline()
