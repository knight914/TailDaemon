# TailDaemon validation

## Scope
Capability-stage experiment only. Neither deb implements Tailscale authentication, WireGuard, tailnet connectivity, routing or DNS.

## Source and build
- Public repo: https://github.com/knight914/TailDaemon
- Branch: feat/utun-probe-20261111
- Version 0.0.2 source: 18c0c9aa9f3df451a0c4494a13a069e4c649b980
- Successful run: https://github.com/knight914/TailDaemon/actions/runs/42872927797
- rootless toolchain: theos/theos at 6e7b8c40e0f5f9f5b2377800dc1e42cd2560d24a
- roothide toolchain: roothide/theos at 958fea4f779943505b15b93c88bb4db8d97b346d
- Both jobs compiled on macos-15-intel with Xcode iPhoneOS SDK.
- rootless package Architecture iphoneos-arm64, executable var/jb/usr/bin/taildaemon-probe.
- roothide package Architecture iphoneos-arm64e, executable usr/bin/taildaemon-probe. CPU target remains arm64; package architecture does not imply arm64e CPU code.
- 0.0.1 rootless built; roothide failed before compilation due to unavailable pinned toolchain tree. Not retried with the same version.

## Runtime observations
- Frida 17.25.1 local socket connected to iOS 16.4.1, arm64, full access.
- Authorized attach to official io.tailscale.ipn.ios reported UID 501 and available exports socket/ioctl/connect/close/getuid/uname.
- Script unloaded and session detached; no hook left active.
- This proves API presence only. No utun was created inside the official app. Sandbox privileges and independent daemon behavior were NOT proven.
- SSH LAN and loopback returned Operation not permitted. No package uploaded or installed, no launch daemon created, no routes/DNS/VPN/authentication modified.

## Follow-up runtime tests
- Separately authorized temporary attach to frida-server PID 7353 reported UID 0. Correct ARM64 variadic ioctl invocation successfully opened PF_SYSTEM, queried utun control, connected and obtained interface utun7. The descriptor was immediately closed successfully. No addresses/routes/DNS were configured. Script unloaded and session detached.
- Initial fixed-argument ioctl declaration produced EFAULT (14); corrected to variadic ABI before retest. This was a probe binding error, not evidence of missing kernel support.
- Separately authorized standalone attempt: extracted the unchanged roothide 0.0.2 executable, copied it to a uniquely created /private/var/tmp directory through a temporary frida-server session, and attempted posix_spawn with output capture. posix_spawn returned 202; no child started. The precise cause is NOT established; do not label this as a verified signature issue without evidence.
- Binary and output were unlinked and temporary directory removed successfully. Script unloaded and session detached. No deb installed, no persistent services, no system signing/security changes, no route/DNS/VPN/authentication changes.
- A root frida-server's utun success does not prove equivalent permission or launch behavior for a new independently signed executable.

## Outstanding
Requires successful authorized independent execution on device to prove utun access. Full iOS Tailscale/router/DNS integration, coexistence, authentication UX, secure storage, and both jailbreak runtime environments remain unimplemented/unverified. These artifacts must not be described as a working Tailscale replacement.
