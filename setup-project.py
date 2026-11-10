from pathlib import Path
import json
p=Path(__file__).resolve().parent
assert str(p)=='/var/minis/shared/github/TailDaemon'
files={
'VERSION':'0.0.1\n',
'build-attempt.json':json.dumps({'version':'0.0.1','scope':'utun capability probe; not a working Tailscale replacement'},indent=2)+'\n',
'Makefile':'''ARCHS = arm64
TARGET = iphone:clang:latest:15.0
include $(THEOS)/makefiles/common.mk
TOOL_NAME = taildaemon-probe
taildaemon-probe_FILES = main.c
taildaemon-probe_CFLAGS = -Wall -Wextra
taildaemon-probe_INSTALL_PATH = /usr/bin
include $(THEOS_MAKE_PATH)/tool.mk
''',
'control':'''Package: com.knight914.taildaemon
Name: TailDaemon Capability Probe
Version: 0.0.1
Architecture: iphoneos-arm64
Description: Temporary utun capability probe. NOT a working Tailscale replacement.
Maintainer: knight914
Author: knight914
Section: Development
''',
'.gitignore':'.theos/\npackages/\ndist/\ntoolchains/\n__pycache__/\n',
'README.md':'''# TailDaemon — capability stage 0.0.1
This project is **not yet a Tailscale client or daemon**. No tailnet authentication or traffic forwarding is implemented.

The arm64 CLI `taildaemon-probe` creates an unconfigured utun interface and immediately closes its descriptor. No addresses, routes, DNS, login data, or persistent services are configured. Run only under an explicitly authorized test. It does not alter the installed Tailscale app.

Two independently built packages: official theos/theos rootless and roothide/theos roothide. Both use the same version. A compiled package is not proof of runtime compatibility. The packages do not install launch daemons and do not start automatically. Uninstall using the package manager; the executable has no persistent state.

Frida probe attaches only to the official Tailscale process, checks exported networking APIs and UID, and unloads/detaches in finally. It does not read credentials. API presence is not proof that an independent root process can create utun or configure system routing.

## Workflow policy
macOS runners, Xcode-provided iPhoneOS SDK, pinned separate Theos revisions. Manual dispatch on development branch. Each compilation attempt requires a new VERSION; two environments share one reservation. Reruns are rejected. Artifacts retain compiler/toolchain and package inspection evidence. No device install is performed by Actions.

## Remaining gates
Independent-process utun access, iOS-specific tailscaled build constraints and router/DNS adaptation, signing and permissions, official-app coexistence, sleep/lock/power behavior, login UX and secure state, true rootless and roothide runtime verification.
'''
}
workflow='''name: Build TailDaemon Probe
on:
  workflow_dispatch:
permissions:
  contents: read
concurrency:
  group: taildaemon-build
  cancel-in-progress: false
jobs:
  reserve:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@11bd71901bbe5b1630ceea73d27597364c9af683
      - name: Check build attempt
        run: |
          test "$GITHUB_RUN_ATTEMPT" = 1
          test "$(cat VERSION)" = "$(python3 -c 'import json; print(json.load(open("build-attempt.json"))["version"])')"
      - uses: actions/cache/restore@5a3ec84eff668545956fd18022155c47e93e2684
        id: reservation
        with:
          path: build-attempt.json
          key: taildaemon-version-${{ hashFiles('VERSION') }}
      - run: test '${{ steps.reservation.outputs.cache-hit }}' != true
      - uses: actions/cache/save@5a3ec84eff668545956fd18022155c47e93e2684
        with:
          path: build-attempt.json
          key: taildaemon-version-${{ hashFiles('VERSION') }}
  build:
    needs: reserve
    runs-on: macos-15-intel
    strategy:
      fail-fast: false
      matrix:
        include:
          - environment: rootless
            repository: theos/theos
            revision: 6e7b8c40e0f5f9f5b2377800dc1e42cd2560d24a
          - environment: roothide
            repository: roothide/theos
            revision: 3ac89c984ec652fd16bcd91b33ae16de45ce76fa
    env:
      THEOS: ${{ github.workspace }}/toolchains/${{ matrix.environment }}
      THEOS_PACKAGE_SCHEME: ${{ matrix.environment }}
    steps:
      - uses: actions/checkout@11bd71901bbe5b1630ceea73d27597364c9af683
      - name: Prepare independent official toolchain
        run: |
          brew install make ldid dpkg
          git clone https://github.com/${{ matrix.repository }} "$THEOS"
          git -C "$THEOS" checkout '${{ matrix.revision }}'
          git -C "$THEOS" submodule update --init --recursive
          mkdir -p "$THEOS/sdks" dist/${{ matrix.environment }}
          ln -s "$(xcrun --sdk iphoneos --show-sdk-path)" "$THEOS/sdks/iPhoneOS$(xcrun --sdk iphoneos --show-sdk-version).sdk"
          { xcodebuild -version; xcrun --sdk iphoneos --show-sdk-version; git -C "$THEOS" rev-parse HEAD; git -C "$THEOS" submodule status --recursive; } > dist/${{ matrix.environment }}/toolchain.txt
      - name: Compile and inspect package
        run: |
          export PATH="$(brew --prefix make)/libexec/gnubin:$PATH"
          make clean package FINALPACKAGE=1
          cp packages/*.deb dist/${{ matrix.environment }}/
          for deb in packages/*.deb; do
            dpkg-deb -I "$deb"
            dpkg-deb -c "$deb"
            dpkg-deb -x "$deb" /tmp/td-package
          done > dist/${{ matrix.environment }}/package-inspection.txt
          python3 - <<'PY'
          import pathlib, subprocess
          for f in pathlib.Path('/tmp/td-package').rglob('taildaemon-probe'):
              for cmd in [['xcrun','lipo','-info',str(f)],['xcrun','otool','-L',str(f)]]:
                  subprocess.run(cmd,check=True)
          PY
      - uses: actions/upload-artifact@ea165f8d65b6e75b540449e92b4886f43607fa02
        with:
          name: TailDaemon-${{ matrix.environment }}-${{ github.run_id }}
          path: dist/${{ matrix.environment }}/
          if-no-files-found: error
          retention-days: 7
'''
# Reservation only on Linux: no software is compiled there.
files['.github/workflows/build.yml']=workflow
for name,text in files.items():
 f=p/name; f.parent.mkdir(parents=True,exist_ok=True); f.write_text(text)
print('Prepared',len(files),'project files')
