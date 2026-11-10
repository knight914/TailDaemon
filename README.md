# TailDaemon — capability stage 0.0.1
This project is **not yet a Tailscale client or daemon**. No tailnet authentication or traffic forwarding is implemented.

The arm64 CLI `taildaemon-probe` creates an unconfigured utun interface and immediately closes its descriptor. No addresses, routes, DNS, login data, or persistent services are configured. Run only under an explicitly authorized test. It does not alter the installed Tailscale app.

Two independently built packages: official theos/theos rootless and roothide/theos roothide. Both use the same version. A compiled package is not proof of runtime compatibility. The packages do not install launch daemons and do not start automatically. Uninstall using the package manager; the executable has no persistent state.

Frida probe attaches only to the official Tailscale process, checks exported networking APIs and UID, and unloads/detaches in finally. It does not read credentials. API presence is not proof that an independent root process can create utun or configure system routing.

## Workflow policy
macOS runners, Xcode-provided iPhoneOS SDK, pinned separate Theos revisions. Manual dispatch on development branch. Each compilation attempt requires a new VERSION; two environments share one reservation. Reruns are rejected. Artifacts retain compiler/toolchain and package inspection evidence. No device install is performed by Actions.

## Remaining gates
Independent-process utun access, iOS-specific tailscaled build constraints and router/DNS adaptation, signing and permissions, official-app coexistence, sleep/lock/power behavior, login UX and secure state, true rootless and roothide runtime verification.
