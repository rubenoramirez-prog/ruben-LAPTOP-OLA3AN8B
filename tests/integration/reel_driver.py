import json
import sys
import os

# Add the skill directory to sys.path so we can import the real logic
skill_path = r"C:\ProyectosIA\instagram-agent-skill\skills\ig-reel"
if skill_path not in sys.path:
    sys.path.append(skill_path)

try:
    from hookscore import run as score_hook
except ImportError as e:
    print(f"Error importing hookscore: {e}")
    sys.exit(1)

def run_reel_skill(prompt):
    """
    Simulates the ig-reel skill process, now using the REAL hookscore logic.
    """
    if "GOOD" in prompt:
        # High-performance hook: Money marker ($), tension marker (lost), specific figure (18,000),
        # and direct address (yours). This should trigger a STRONG score.
        spoken_hook = "I lost $18,000 on one missing contract clause. Here is how to fix yours."
        on_screen_hook = "$18,000 MISTAKE"
        script = "I lost $18,000 on one missing contract clause. Here is how to fix yours. Most coaches use a template they found online. I learned the hard way that one sentence can cost you everything. Here is the specific clause you need. Grab it in my bio."
    else:
        # Intentional failure: Greeting, vague, long
        spoken_hook = "Hello everyone! In this video I will show you a secret hack to unlock your potential."
        on_screen_hook = "UNLOCK YOUR POTENTIAL NOW WITH THIS HACK"
        script = "Hello everyone! In this video I will show you a secret hack to unlock your potential. It is a game changer for your life. Just follow me for more tips."

    # USE REAL LOGIC HERE
    results, overall, verdict, flags = score_hook(spoken_hook)

    return {
        "hook_spoken": spoken_hook,
        "hook_on_screen": on_screen_hook,
        "score": overall,
        "verdict": verdict,
        "flags": flags,
        "script": script,
        "beats": [
            {"time": "0:00-0:02", "text": spoken_hook, "type": "HOOK"},
        ],
        "loop": "Contract." if "GOOD" in prompt else ""
    }

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python reel_driver.py 'prompt'")
        sys.exit(1)

    prompt = sys.argv[1]
    result = run_reel_skill(prompt)

    with open("test_output.json", "w") as f:
        json.dump(result, f, indent=2)
    print(f"Output saved to test_output.json (Score: {result['score']})")
