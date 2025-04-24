import os, sys, json, re, datetime, subprocess, pathlib
import google.generativeai as genai

# --------------------------------------------------
# 引数（Evaluate pun ワークフローから渡される）
# --------------------------------------------------
issue_number = sys.argv[1]  # GitHub Issue 番号
repo         = sys.argv[2]  # repo フル名 e.g. "zin1985/dajare_garden"
user_login   = sys.argv[3]  # Issue 作成者の GitHub ID

# --------------------------------------------------
# 1. イベント JSON から Issue 本文を取得（UTF-8 安全）
# --------------------------------------------------
event_file = pathlib.Path(os.environ["GITHUB_EVENT_PATH"])
with event_file.open(encoding="utf-8") as f:
    body = json.load(f)["issue"]["body"]

# --------------------------------------------------
# 2. 本文行ごとにフィルタして “ダジャレ部” を取る
#    - "名前" や "ダジャレ" の見出し行（Markdown # やラベル行）を除外
# --------------------------------------------------
lines = body.splitlines()
pun_lines = []
for line in lines:
    # 除外パターン: 見出し (#, *, >) に「名前」か「ダジャレ」が含まれる行
    if re.match(r'^\s*[#>*\-\*]+\s*(名前|ダジャレ)', line):
        continue
    # 除外パターン: 空行と「名前: さとう」のような行
    if re.match(r'^\s*(名前:|ダジャレ:)', line):
        continue
    # それ以外はダジャレの可能性がある行として追加
    pun_lines.append(line)

pun = "\n".join(pun_lines).strip() or body.strip()
name = user_login  # Azure上では別途名前を取れないため GitHub ID を使用

# --------------------------------------------------
# 3. Gemini にダジャレを採点してもらう
# --------------------------------------------------
genai.configure(api_key=os.environ["GOOGLE_API_KEY"])
model = genai.GenerativeModel("gemini-1.5-pro-latest")

prompt = (
    "あなたはダジャレ評論家です。次の日本語ダジャレを100点満点で"
    "数値だけ返してください。\n\n" + pun
)
resp = model.generate_content(prompt)
m    = re.search(r"\d+", resp.text)
score = int(m.group(0)) if m else 50

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
# 5. GitHub にコミット & プッシュ
# --------------------------------------------------
subprocess.run(["git", "config", "user.name", "github-actions"])
subprocess.run(["git", "config", "user.email", "actions@github.com"])
subprocess.run(["git", "add", path])
subprocess.run(
    ["git", "commit", "-m", f"Add pun from issue #{issue_number}"],
    stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL
)
subprocess.run(["git", "push"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
