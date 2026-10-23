import json
import subprocess
import os
import sys

def run_humanize_test(prompt):
    """
    Simulates the humanization process:
    Raw Draft -> humanize.py -> Clean Draft -> detect.py
    """
    if "GOOD" in prompt:
        # Text that is already mostly human
        raw_text = "I spent ten years in the agency world. Here is why most proposal templates fail. They are too generic. You need one specific line that proves you know the client's pain."
    else:
        # Text designed to be high-slop/machine
        # Includes: Em-dash, curly quotes, "delve", "unlock your potential", and "in today's fast-paced world"
        raw_text = "In today's fast-paced world, we must delve into the essence of growth — it is a testament to our resilience. “Unlock your potential” by leveraging these tools. It is a seamless experience."

    # Write the raw draft to a file
    with open("draft_raw.txt", "w", encoding="utf-8") as f:
        f.write(raw_text)

    # 1. Run humanize.py
    # command: python humanize.py draft.txt -o clean.txt --json
    skill_path = r"C:\ProyectosIA\instagram-agent-skill\skills\ig-human"
    humanize_cmd = f'python "{os.path.join(skill_path, "humanize.py")}" draft_raw.txt --json'
    humanize_out = subprocess.check_output(humanize_cmd, shell=True, encoding="utf-8")
    humanize_data = json.loads(humanize_out)
    clean_text = humanize_data["text"]

    with open("draft_clean.txt", "w", encoding="utf-8") as f:
        f.write(clean_text)

    # 2. Run detect.py on raw
    detect_raw_cmd = f'python "{os.path.join(skill_path, "detect.py")}" draft_raw.txt --json'
    detect_raw_out = subprocess.check_output(detect_raw_cmd, shell=True, encoding="utf-8")
    raw_score = json.loads(detect_raw_out)

    # 3. Run detect.py on clean
    detect_clean_cmd = f'python "{os.path.join(skill_path, "detect.py")}" draft_clean.txt --json'
    detect_clean_out = subprocess.check_output(detect_clean_cmd, shell=True, encoding="utf-8")
    clean_score = json.loads(detect_clean_out)

    return {
        "raw": {
            "text": raw_text,
            "score": raw_score["human_score"],
            "verdict": raw_score["verdict"],
            "checks": raw_score["checks"]
        },
        "clean": {
            "text": clean_text,
            "score": clean_score["human_score"],
            "verdict": clean_score["verdict"],
            "checks": clean_score["checks"]
        },
        "delta": clean_score["human_score"] - raw_score["human_score"]
    }

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python humanize_driver.py 'prompt'")
        sys.exit(1)

    prompt = sys.argv[1]
    result = run_humanize_test(prompt)

    with open("humanize_test_output.json", "w") as f:
        json.dump(result, f, indent=2)
    print(f"Humanization complete. Delta: {result['delta']:.2f}")
