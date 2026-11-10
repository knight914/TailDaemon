import frida, json, threading
source = r'''
const address = n => Module.getGlobalExportByName(n);
const uid = new NativeFunction(address('getuid'), 'uint', []);
const socket = new SystemFunction(address('socket'), 'int', ['int','int','int']);
const ioctl = new SystemFunction(address('ioctl'), 'int', ['int','ulong','...','pointer']);
const connect = new SystemFunction(address('connect'), 'int', ['int','pointer','uint']);
const getsockopt = new SystemFunction(address('getsockopt'), 'int', ['int','int','int','pointer','pointer']);
const close = new SystemFunction(address('close'), 'int', ['int']);
const report = {uid:uid(), arch:Process.arch, stages:[], fdClosed:false};
let fd = -1;
try {
  let r = socket(32, 2, 2); // PF_SYSTEM, SOCK_DGRAM, SYSPROTO_CONTROL
  report.stages.push({stage:'socket',result:r.value,errno:r.errno});
  if (r.value < 0) throw new Error('socket failed');
  fd = r.value;
  const info = Memory.alloc(100); info.writeByteArray(new Uint8Array(100));
  info.add(4).writeUtf8String('com.apple.net.utun_control');
  r = ioctl(fd, 0xc0644e03, info); // _IOWR('N',3,struct ctl_info)
  report.stages.push({stage:'CTLIOCGINFO',result:r.value,errno:r.errno});
  if (r.value < 0) throw new Error('ioctl failed');
  const ctl = Memory.alloc(32); ctl.writeByteArray(new Uint8Array(32));
  ctl.writeU8(32); ctl.add(1).writeU8(32); ctl.add(2).writeU16(2);
  ctl.add(4).writeU32(info.readU32()); // unit 0 requests unused interface
  r = connect(fd,ctl,32);
  report.stages.push({stage:'connect',result:r.value,errno:r.errno});
  if (r.value < 0) throw new Error('utun connect failed');
  const name = Memory.alloc(64); const length = Memory.alloc(4); length.writeU32(64);
  r = getsockopt(fd,2,2,name,length);
  report.stages.push({stage:'UTUN_OPT_IFNAME',result:r.value,errno:r.errno});
  if (r.value === 0) report.interface = name.readUtf8String();
} catch (e) { report.error = String(e); }
finally {
  if (fd >= 0) { const r = close(fd); report.fdClosed = r.value === 0; report.closeErrno = r.errno; }
  send(report);
}
'''
session = script = None
finished = threading.Event()
try:
    device = frida.get_device_manager().get_device('socket',timeout=5)
    targets = [p for p in device.enumerate_processes() if p.name == 'frida-server']
    if len(targets) != 1: raise RuntimeError('Expected exactly one frida-server')
    print('TARGET', targets[0].pid, targets[0].name, flush=True)
    session = device.attach(targets[0].pid)
    script = session.create_script(source)
    def message(m, data):
        print(json.dumps(m),flush=True)
        finished.set()
    script.on('message', message)
    script.load()
    if not finished.wait(10): raise RuntimeError('No probe result in 10 seconds')
finally:
    try:
        if script is not None: script.unload(); print('SCRIPT_UNLOADED',flush=True)
    finally:
        if session is not None: session.detach(); print('SESSION_DETACHED',flush=True)
