"""python3 Art/Source/Ella/Paint/paint.py <piece> <round>  (one paid Gemini call, prompt from prompts.json)"""
import json, subprocess, sys, os
n, r = sys.argv[1], sys.argv[2]
d = os.path.dirname(os.path.abspath(__file__))
p = json.load(open(os.path.join(d, "prompts.json")))[n]
out = f"pipeline/art/proof/artella/{n}/{r}/{n}.png"
os.makedirs(os.path.dirname(out), exist_ok=True)
cmd = ["python3", "tools/assetgen.py", "image", "--provider", "gemini", "--prompt", p, "--out", out, "--aspect", "21:9",
       "--image-size", "2K", "--model", "gemini-3-pro-image-preview", "--element", "character"]
if n != "closed":
    cmd += ["--input", "pipeline/art/proof/ImageProof/R3/ref_umbrella.png"]
sys.exit(subprocess.run(cmd).returncode)
