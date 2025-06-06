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
# 3. 本文から名前とダジャレを正確に分離抽出
# --------------------------------------------------
name = user_login  # fallback
pun = ""

# Markdown構造に従って抽出
match_name = re.search(r"###\s*名前\s*\n(.*?)\n", issue_body, re.DOTALL)
match_pun  = re.search(r"###\s*ダジャレ\s*\n(.*)", issue_body, re.DOTALL)

if match_name:
    name = match_name.group(1).strip()
if match_pun:
    pun = match_pun.group(1).strip()

# --------------------------------------------------
# 4. Gemini に採点依頼
# --------------------------------------------------
import google.generativeai as genai
genai.configure(api_key=os.environ["GOOGLE_API_KEY"])
model = genai.GenerativeModel("gemini-1.5-pro-latest")

score_prompt = (
    "あなたは熟練のダジャレ評論家です。以下のダジャレを見て、以下の基準に従って厳密に100点満点で採点してください。\n\n"
    "評価基準：\n"
    "1. 語呂合わせの巧妙さ（意味の二重性や意外性）\n"
    "2. 日本語として自然か（不自然な文構造は減点）\n"
    "3. シンプルながら面白いか（短くてもウケるなら高得点）\n"
    "4. 新鮮さ・独自性（既出ネタやありきたり感は減点）\n"
    "5. 聞き手の笑いを誘うインパクト（シュール・高度問わず）\n\n"
    "ルール：\n"
    "- 採点は0点～100点の範囲で行い、0点は最低評価（完全にスベっているもの）、100点は殿堂入り級の傑作とします\n\n"
    "その評価理由を簡潔に1文でコメントしてください。\n\n"
    "※ただし、コメントは遠慮せずに **辛口に** 書いてください。\n"
    "・つまらないダジャレには容赦なくダメ出しをしてください\n"
    "・ベタすぎる／既視感がある／寒い／ひねりがない など、正直な指摘を歓迎します\n"
    "・面白い場合も、必ず何か厳しめの改善点を含めてください\n\n"
    "必ず以下の出力形式を守る：\n"
    "点数（例: 85）\n"
    "コメント（例: 語呂のインパクトはあるが少しベタ）\n\n"
    f"ダジャレ：\n{pun}"
)
resp = model.generate_content(score_prompt)
lines = resp.text.strip().splitlines()
score = int(re.search(r"\d+", lines[0]).group(0))
comment = lines[1].strip() if len(lines) > 1 else ""

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

records.append({"name": name, "pun": pun, "score": score, "comment": comment})
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
