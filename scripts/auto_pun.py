import os, json, datetime, re, subprocess, google.generativeai as genai
genai.configure(api_key=os.environ['GOOGLE_API_KEY'])
model = genai.GenerativeModel('gemini-1.5-pro-latest')
pun = model.generate_content("日本語で高度なダジャレを1つだけ生成してください。").text.strip()

score_resp = model.generate_content(f"次の日本語ダジャレを100点満点で数値だけ返してください。\\n\\n{pun}")
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
