import os, json, datetime, re, subprocess, google.generativeai as genai
genai.configure(api_key=os.environ['GOOGLE_API_KEY'])
model = genai.GenerativeModel('gemini-1.5-pro-latest')
# ダジャレ生成プロンプト（ユニークで秀逸なものを求める）
pun_prompt = (
    "日本語でユニークで高度なダジャレを1つだけ生成してください。\n"
    "・語呂合わせが巧妙なもの\n"
    "・聞き手がクスッと笑うようなシュールさや意外性があるもの\n"
    "・可能であれば短めでインパクトのある表現\n"
    "・既出の使い古されたネタは避けてください\n\n"
    "例：\n"
    "・布団が吹っ飛んだ\n"
    "・カレーは辛ぇ〜\n"
    "・オクラが怒られた\n\n"
    "ダジャレ："
)
pun = model.generate_content(pun_prompt).text.strip()

# 採点プロンプト（詳細な評価基準付き・数値のみで返す）
score_prompt = (
    "あなたは熟練のダジャレ評論家です。以下のダジャレを見て、以下の基準に従って厳密に100点満点で採点してください。\n\n"
    "評価基準：\n"
    "1. 語呂合わせの巧妙さ（意味の二重性や意外性）\n"
    "2. 日本語として自然か（不自然な文構造は減点）\n"
    "3. シンプルながら面白いか（短くてもウケるなら高得点）\n"
    "4. 新鮮さ・独自性（既出ネタやありきたり感は減点）\n"
    "5. 聞き手の笑いを誘うインパクト（シュール・高度問わず）\n\n"
    "ルール：\n"
    "- 必ず **数値のみで1行に1つ** 出力してください（コメントや説明は不要）\n"
    "- 採点は0点～100点の範囲で行い、0点は最低評価（完全にスベっているもの）、100点は殿堂入り級の傑作とします\n\n"
    "ダジャレ：\n" + pun
)

score_resp = model.generate_content(score_prompt)
m = re.search(r'\d+', score_resp.text)
score = int(m.group(0)) if m else 50

today = datetime.date.today().isoformat()
path = f"data/{today}.json"
os.makedirs('data', exist_ok=True)
data = []
if os.path.exists(path):
    data = json.load(open(path, encoding='utf-8'))
data.append({'name':'Gemini','pun':pun,'score':score})
with open(path, 'w', encoding='utf-8') as f:
    json.dump(data, f, ensure_ascii=False, indent=2)

subprocess.run(['git','config','user.name','github-actions'])
subprocess.run(['git','config','user.email','actions@github.com'])
subprocess.run(['git','add', path])
subprocess.run(['git','commit','-m','Gemini auto pun'])
subprocess.run(['git','push'])
