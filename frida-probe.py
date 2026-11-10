import frida, json
script_source = r'''
const sym = n => Module.getGlobalExportByName(n);
const out = {arch: Process.arch, platform: Process.platform, APIs:{}};
for (const n of ['socket','ioctl','connect','close','getuid','uname']) {
 try {out.APIs[n] = !!sym(n);} catch (_) {out.APIs[n] = false;}
}
out.uid = new NativeFunction(sym('getuid'),'uint',[])();
// Only inspect API availability. No credentials, packets, routes or VPN state.
send(out);
'''
session = None
script = None
try:
    device = frida.get_device_manager().get_device('socket', timeout=5)
    apps = [a for a in device.enumerate_applications() if a.identifier == 'io.tailscale.ipn.ios']
    if len(apps) != 1 or not apps[0].pid:
        raise RuntimeError('Official Tailscale application is not running')
    print('TARGET', apps[0].identifier, apps[0].pid)
    session = device.attach(apps[0].pid)
    script = session.create_script(script_source)
    script.on('message', lambda message,data: print(json.dumps(message)))
    script.load()
finally:
    try:
        if script is not None: script.unload(); print('SCRIPT_UNLOADED')
    finally:
        if session is not None: session.detach(); print('SESSION_DETACHED')
