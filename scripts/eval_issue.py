import os, sys, json, re, datetime, subprocess, pathlib
import google.generativeai as genai

# --------------------------------------------------
# 引数（Evaluate pun ワークフローから渡される）
# --------------------------------------------------
issue_number = sys.argv[1]  # GitHub Issue 番号
repo         = sys.argv[2]  # repo フル名 例: zin1985/dajare_garden
user_login   = sys.argv[3]  # Issue 作成者の GitHub ID

# --------------------------------------------------
# 1. イベント JSON から Issue 本文を取得（UTF-8 で安全）
# --------------------------------------------------
event_file   = pathlib.Path(os.environ["GITHUB_EVENT_PATH"])
with event_file.open(encoding="utf-8") as f:
    issue_body = json.load(f)["issue"]["body"]

# --------------------------------------------------
# 2. 名前とダジャレを抽出（行頭 ^ で見出し行を除外）
# --------------------------------------------------
name_match = re.search(r'^###\s*名前\s*\r?\n+([^\r\n]+)', issue_body, re.M)
pun_match  = re.search(r'^###\s*ダジャレ\s*\r?\n+([\s\S]+)', issue_body, re.M)

name = name_match.group(1).strip() if name_match else user_login
pun  = pun_match.group(1).strip()  if pun_match  else issue_body.strip()

# --------------------------------------------------
# 3. Gemini で採点
# --------------------------------------------------
genai.configure(api_key=os.environ["GOOGLE_API_KEY"])
model = genai.GenerativeModel("gemini-1.5-pro-latest")

prompt = (
    "あなたはダジャレ評論家です。次の日本語ダジャレを100点満点で数値だけ返してください。\n\n"
    + pun
)
resp   = model.generate_content(prompt)
m      = re.search(r"\d+", resp.text)
score  = int(m.group(0)) if m else 50

# --------------------------------------------------
# 4. data/YYYY-MM-DD.json に追記
# --------------------------------------------------
today = datetime.date.today().isoformat()
path  = f"data/{today}.json"
os.makedirs("data", exist_ok=True)

data = []
if os.path.exists(path):
    with open(path, encoding="utf-8") as f:
        data = json.load(f)

data.append({"name": name, "pun": pun, "score": score})

with open(path, "w", encoding="utf-8") as f:
    json.dump(data, f, ensure_ascii=False, indent=2)

# --------------------------------------------------
# 5. Git にコミット & プッシュ
# --------------------------------------------------
subprocess.run(["git", "config", "user.name", "github-actions"])
subprocess.run(["git", "config", "user.email", "actions@github.com"])
subprocess.run(["git", "add", path])
subprocess.run(["git", "commit", "-m", f"Add pun from issue #{issue_number}"])
subprocess.run(["git", "push"])
