// TailDaemon 0.0.1: capability probe, NOT a Tailscale client.
// Creates an unconfigured utun interface, prints its name, then closes it.
// Never changes addresses, routes, DNS, VPN state, or authentication.
#include <stdio.h>
#include <string.h>
#include <errno.h>
#include <unistd.h>
#include <sys/socket.h>
#include <sys/ioctl.h>
#include <stdint.h>
// Public XNU kernel-control ABI; some iPhoneOS SDKs omit these headers.
#ifndef SYSPROTO_CONTROL
#define SYSPROTO_CONTROL 2
#endif
#ifndef AF_SYS_CONTROL
#define AF_SYS_CONTROL 2
#endif
struct ctl_info { uint32_t ctl_id; char ctl_name[96]; };
struct sockaddr_ctl {
    uint8_t sc_len; uint8_t sc_family; uint16_t ss_sysaddr;
    uint32_t sc_id; uint32_t sc_unit; uint32_t sc_reserved[5];
};
#define CTLIOCGINFO _IOWR('N', 3, struct ctl_info)
#define TD_UTUN_OPT_IFNAME 2
int main(void) {
    printf("TailDaemon capability probe 0.0.1 uid=%u\n", (unsigned)getuid());
    int fd = socket(PF_SYSTEM, SOCK_DGRAM, SYSPROTO_CONTROL);
    if (fd < 0) { perror("socket(PF_SYSTEM)"); return 1; }
    struct ctl_info info;
    memset(&info, 0, sizeof(info));
    snprintf(info.ctl_name, sizeof(info.ctl_name), "com.apple.net.utun_control");
    if (ioctl(fd, CTLIOCGINFO, &info) < 0) { perror("CTLIOCGINFO"); close(fd); return 2; }
    struct sockaddr_ctl addr;
    memset(&addr, 0, sizeof(addr));
    addr.sc_len = sizeof(addr);
    addr.sc_family = AF_SYSTEM;
    addr.ss_sysaddr = AF_SYS_CONTROL;
    addr.sc_id = info.ctl_id;
    addr.sc_unit = 0;
    if (connect(fd, (struct sockaddr *)&addr, sizeof(addr)) < 0) {
        perror("connect(utun)"); close(fd); return 3;
    }
    char name[64] = {0};
    socklen_t length = sizeof(name);
    if (getsockopt(fd, SYSPROTO_CONTROL, TD_UTUN_OPT_IFNAME, name, &length) < 0) {
        perror("UTUN_OPT_IFNAME"); close(fd); return 4;
    }
    printf("Created unconfigured interface: %s\n", name);
    if (close(fd) < 0) { perror("close"); return 5; }
    puts("Closed interface. No routes or DNS configured. This does not prove Tailscale connectivity.");
    return 0;
}
