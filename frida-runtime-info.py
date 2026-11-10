import frida,json,threading
src=r'''
const matches=Process.enumerateModules().filter(m=>/roothid|jailbreak|systemhook|frida-server|libroot/i.test(m.path));
const out={modules:matches.map(m=>({name:m.name,path:m.path})),metadata:[]};
// Read only selected package metadata, never package databases or personal logs.
const roots=new Set();
for(const m of matches){const x=m.path.match(/^(.*?\\.jbroot-[^/]+)/);if(x)roots.add(x[1]);const i=m.path.indexOf('/basebin/');if(i>0)roots.add(m.path.slice(0,i));}
for(const root of roots){
 for(const rel of ['/basebin/.version','/basebin/version','/var/lib/dpkg/info/dopamine.control','/var/lib/dpkg/info/roothide.control']){
  try{const s=File.readAllText(root+rel);if(s.length<8192)out.metadata.push({path:root+rel,text:s});}catch(_){}
 }
}
send(out);
'''
session=script=None;done=threading.Event()
try:
 d=frida.get_device_manager().get_device('socket',timeout=5)
 p=[p for p in d.enumerate_processes() if p.name=='frida-server']
 if len(p)!=1:raise RuntimeError('Expected one frida-server')
 session=d.attach(p[0].pid);script=session.create_script(src)
 def msg(m,data):print(json.dumps(m,ensure_ascii=False),flush=True);done.set()
 script.on('message',msg);script.load()
 if not done.wait(8):raise RuntimeError('No result')
finally:
 try:
  if script:script.unload();print('SCRIPT_UNLOADED')
 finally:
  if session:session.detach();print('SESSION_DETACHED')
