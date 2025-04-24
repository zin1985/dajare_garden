import os, sys, json, re, datetime, subprocess, textwrap
import google.generativeai as genai

issue_number = sys.argv[1]
repo = sys.argv[2]
user_login = sys.argv[3]

# read issue content via environment
issue_body = os.environ.get('ISSUE_BODY', '')
name_match = re.search(r'^###\s*名前\s*\r?\n+([^\r\n]+)', issue_body, re.M)
pun_match  = re.search(r'^###\s*ダジャレ\s*\r?\n+([\s\S]+)', issue_body, re.M)

name = name_match.group(1).strip() if name_match else sys.argv[3]
pun  = pun_match.group(1).strip()  if pun_match  else issue_body.strip()

genai.configure(api_key=os.environ['GOOGLE_API_KEY'])
model = genai.GenerativeModel('gemini-1.5-pro-latest')

prompt = f"あなたはダジャレ評論家です。次の日本語ダジャレを100点満点で数値だけ返してください。\\n\\n{pun}"
resp = model.generate_content(prompt)
m = re.search(r'\d+', resp.text)
score = int(m.group(0)) if m else 50

today = datetime.date.today().isoformat()
path = f"data/{today}.json"
os.makedirs('data', exist_ok=True)
data = []
if os.path.exists(path):
    data = json.load(open(path, encoding='utf-8'))
data.append({'name': name, 'pun': pun, 'score': score})
with open(path, 'w', encoding='utf-8') as f:
    json.dump(data, f, ensure_ascii=False, indent=2)

subprocess.run(['git','config','user.name','github-actions'])
subprocess.run(['git','config','user.email','actions@github.com'])
subprocess.run(['git','add', path])
subprocess.run(['git','commit','-m', f'Add pun from issue #{issue_number}'])
subprocess.run(['git','push'])
