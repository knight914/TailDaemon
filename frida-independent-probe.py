import frida, json
from pathlib import Path
source = r'''
const fn=(n,r,a)=>new SystemFunction(Module.getGlobalExportByName(n),r,a);
const close=fn('close','int',['int']);
const unlink=fn('unlink','int',['pointer']);
const rmdir=fn('rmdir','int',['pointer']);
const open=fn('open','int',['pointer','int','...','int']);
const write=fn('write','long',['int','pointer','ulong']);
const read=fn('read','long',['int','pointer','ulong']);
const chmod=fn('chmod','int',['pointer','uint']);
const mkdtemp=fn('mkdtemp','pointer',['pointer']);
const init=fn('posix_spawn_file_actions_init','int',['pointer']);
const destroy=fn('posix_spawn_file_actions_destroy','int',['pointer']);
const addopen=fn('posix_spawn_file_actions_addopen','int',['pointer','int','pointer','int','uint']);
const dup2=fn('posix_spawn_file_actions_adddup2','int',['pointer','int','int']);
const spawn=fn('posix_spawn','int',['pointer','pointer','pointer','pointer','pointer','pointer']);
const waitpid=fn('waitpid','int',['int','pointer','int']);
rpc.exports = {run: async function(bytes) {
 const result={}; let dir=null,path=null,log=null,fd=-1,actions=null,child=0,reaped=false;
 try {
  dir=Memory.allocUtf8String('/private/var/tmp/taildaemon-probe-XXXXXX');
  if(mkdtemp(dir).value.isNull()) throw Error('mkdtemp failed');
  path=Memory.allocUtf8String(dir.readUtf8String()+'/probe');
  log=Memory.allocUtf8String(dir.readUtf8String()+'/output');
  let r=open(path,0xa01,448); if(r.value<0) throw Error('open: '+r.errno); fd=r.value;
  const data=Memory.alloc(bytes.byteLength);data.writeByteArray(bytes);
  r=write(fd,data,bytes.byteLength);if(r.value.toNumber()!==bytes.byteLength) throw Error('short write');
  close(fd);fd=-1;
  if(chmod(path,448).value!==0) throw Error('chmod failed');
  actions=Memory.alloc(Process.pointerSize);r=init(actions);if(r.value!==0) throw Error('spawn actions init '+r.value);
  r=addopen(actions,1,log,0xa01,384);if(r.value!==0) throw Error('spawn addopen '+r.value);
  r=dup2(actions,1,2);if(r.value!==0) throw Error('spawn dup2 '+r.value);
  const argv=Memory.alloc(2*Process.pointerSize);argv.writePointer(path);argv.add(Process.pointerSize).writePointer(NULL);
  const env=Memory.alloc(Process.pointerSize);env.writePointer(NULL);
  const pid=Memory.alloc(4);r=spawn(pid,path,actions,NULL,argv,env);result.spawnError=r.value;
  if(r.value!==0) throw Error('posix_spawn rejected: '+r.value);
  child=pid.readS32();result.pid=child;
  const status=Memory.alloc(4);
  for(let i=0;i<100;i++) {
   r=waitpid(child,status,1);
   if(r.value===child){reaped=true;result.waitStatus=status.readS32();break;}
   if(r.value<0){result.waitErrno=r.errno;break;}
   await new Promise(resolve=>setTimeout(resolve,50));
  }
  result.reaped=reaped;
  if(!reaped) throw Error('child status not collected; no termination attempted');
  r=open(log,0,0);if(r.value>=0){fd=r.value;const buf=Memory.alloc(8192);const n=read(fd,buf,8191).value.toNumber();if(n>=0){buf.add(n).writeU8(0);result.output=buf.readUtf8String();}close(fd);fd=-1;}
 } catch(e){result.error=String(e);}
 finally {
  if(fd>=0)close(fd);
  if(actions)destroy(actions);
  result.cleanup={};
  if(path)result.cleanup.binaryUnlinked=unlink(path).value===0;
  if(log)result.cleanup.logUnlinked=unlink(log).value===0;
  if(dir)result.cleanup.directoryRemoved=rmdir(dir).value===0;
 }
 return result;
}};
'''
p=Path(__file__).resolve().parent
binary=p/'dist/0.0.2/TailDaemon-roothide-42872927797/taildaemon-probe'
session=script=None
try:
 d=frida.get_device_manager().get_device('socket',timeout=5)
 ps=[x for x in d.enumerate_processes() if x.name=='frida-server']
 if len(ps)!=1:raise RuntimeError('Expected one frida-server')
 session=d.attach(ps[0].pid);script=session.create_script(source)
 script.on('message',lambda m,data:print(json.dumps(m),flush=True))
 script.load()
 print(json.dumps(script.exports_sync.run(binary.read_bytes()),ensure_ascii=False,indent=2),flush=True)
finally:
 try:
  if script:script.unload();print('SCRIPT_UNLOADED',flush=True)
 finally:
  if session:session.detach();print('SESSION_DETACHED',flush=True)
