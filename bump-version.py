from pathlib import Path
import json
p=Path(__file__).resolve().parent
assert str(p)=='/var/minis/shared/github/TailDaemon'
assert (p/'VERSION').read_text().strip()=='0.0.1'
for name in ['control','main.c']:
 f=p/name
 f.write_text(f.read_text().replace('0.0.1','0.0.2'))
(p/'VERSION').write_text('0.0.2\n')
(p/'build-attempt.json').write_text(json.dumps({'version':'0.0.2','previous_run':42869003394,'reason':'Unavailable roothide toolchain revision; pin current verified upstream revision','scope':'utun probe only'},indent=2)+'\n')
f=p/'.github/workflows/build.yml'
s=f.read_text(); assert '3ac89c984ec652fd16bcd91b33ae16de45ce76fa' in s
f.write_text(s.replace('3ac89c984ec652fd16bcd91b33ae16de45ce76fa','958fea4f779943505b15b93c88bb4db8d97b346d'))
print('Reserved 0.0.2')
