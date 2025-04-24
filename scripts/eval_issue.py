import os, sys, json, re, datetime, subprocess
from urllib.request import Request, urlopen

# --------------------------------------------------
# 1. 引数取得
# --------------------------------------------------
issue_number = sys.argv[1]  # Issue 番号
repo         = sys.argv[2]  # "owner/repo"
user_login   = sys.argv[3]  # 投稿者 GitHub ID

# --------------------------------------------------
# 2. GitHub REST API で本文を取得
# --------------------------------------------------
token = os.environ.get("GITHUB_TOKEN")
if not token:
    print("Error: GITHUB_TOKEN not set", file=sys.stderr)
    sys.exit(1)

url = f"https://api.github.com/repos/{repo}/issues/{issue_number}"
req = Request(url, headers={
    "Authorization": f"Bearer {token}",
    "User-Agent": "dajare-issue-bot/1.0",
    "Accept": "application/vnd.github+json"
})
with urlopen(req) as r:
    issue_body = json.load(r).get("body", "")

# --------------------------------------------------
# 3. 本文からダジャレ行を抽出
# --------------------------------------------------
lines = issue_body.splitlines()
pun_lines = []
for line in lines:
    # 見出し行やラベル行を除去
    if re.match(r'^\s*[#>*\-\*]+\s*(名前|ダジャレ)', line):
        continue
    if re.match(r'^\s*(名前:|ダジャレ:)', line):
        continue
    pun_lines.append(line)

pun = "\n".join(pun_lines).strip() or issue_body.strip()
name = user_login

# --------------------------------------------------
# 4. Gemini に採点依頼
# --------------------------------------------------
import google.generativeai as genai
genai.configure(api_key=os.environ["GOOGLE_API_KEY"])
model = genai.GenerativeModel("gemini-1.5-pro-latest")

prompt = (
    "あなたはダジャレ評論家です。次の日本語ダジャレを100点満点で"
    "数値だけ返してください。\n\n" + pun
)
resp = model.generate_content(prompt)
m = re.search(r"\d+", resp.text)
score = int(m.group(0)) if m else 50

# --------------------------------------------------
# 5. JSON に記録
# --------------------------------------------------
today = datetime.date.today().isoformat()
path  = f"data/{today}.json"
os.makedirs("data", exist_ok=True)

records = []
if os.path.exists(path):
    with open(path, encoding="utf-8") as f:
        records = json.load(f)

records.append({"name": name, "pun": pun, "score": score})
with open(path, "w", encoding="utf-8") as f:
    json.dump(records, f, ensure_ascii=False, indent=2)

# --------------------------------------------------
# 6. コミット&プッシュ
# --------------------------------------------------
subprocess.run(["git", "config", "user.name", "github-actions"])
subprocess.run(["git", "config", "user.email", "actions@github.com"])
subprocess.run(["git", "add", path])
subprocess.run(["git", "commit", "-m", f"Add pun from issue #{issue_number}"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
subprocess.run(["git", "push"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
