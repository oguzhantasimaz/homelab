# 🏠 Dell 7567 Proxmox Homelab

> 🌐 **English** | [Türkçe](README.tr.md)

A guide to turning an old Dell Inspiron 7567 gaming laptop into a fully-featured home server. DPI bypass gateway, media server, smart home control, photo backup, file management, and remote access — all on a single machine.

Includes a Zapret gateway optimized to bypass DPI blocks (Discord, YouTube, etc.) imposed by ISPs in Turkey (Superonline, Türk Telekom, etc.).

## 📋 Hardware

| Component | Detail |
|-----------|--------|
| **Laptop** | Dell Inspiron 7567 |
| **CPU** | Intel Core i7-7700HQ (4C/8T @ 2.80GHz) |
| **RAM** | 16GB DDR4 |
| **iGPU** | Intel HD Graphics 630 (Jellyfin VAAPI) |
| **dGPU** | NVIDIA GTX 1050 Ti Mobile (device nodes bound into Jellyfin LXC 101; Ollama planned) |
| **Webcam** | Realtek Integrated Webcam (0bda:568a) |
| **SSD** | 128GB SanDisk X400 (Proxmox OS + LVM) |
| **HDD** | 1TB ext4 (VM/LXC disks, incomplete downloads) |
| **USB HDD** | 5TB ext4 (media, Immich, backups, general storage) |
| **Ethernet** | USB Ethernet Adapter (100Mbps negotiated) |
| **Hypervisor** | Proxmox VE 9.1.1 (kernel 6.17.2-1-pve) |
| **Router** | Keenetic Titan (PPPoE) |
| **ISP** | Superonline Fiber |

### Client Devices

- Windows 11 PC
- iPhone 14 Pro
- MacBook Pro M1 Pro

## 🏗️ Architecture

```
┌──────────────────────────────────────────────────────────────────────────┐
│                          Proxmox VE Host (pve)                           │
│                          192.168.1.100 (vmbr0)                           │
│                Tailscale (subnet router, 192.168.1.0/24)                 │
│                      Filebrowser (:8085 → 5TB ext4)                      │
│                                                                          │
│  ┌─────────┐ ┌─────────┐ ┌─────────┐ ┌─────────┐ ┌─────────┐ ┌─────────┐ │
│  │ LXC 100 │ │ LXC 101 │ │ LXC 102 │ │ LXC 104 │ │ LXC 105 │ │ LXC 106 │ │
│  │  Zapret │ │ Jellyfin│ │Arr Stack│ │  Immich │ │   Apps  │ │  Gozcu  │ │
│  │ Gateway │ │  + GPU  │ │ + Docker│ │ + Photos│ │ + Docker│ │ crawler │ │
│  │   priv  │ │  unpriv │ │  unpriv │ │   priv  │ │  unpriv │ │  unpriv │ │
│  │   .101  │ │   .102  │ │   .103  │ │   .105  │ │   .108  │ │   .106  │ │
│  └─────────┘ └─────────┘ └─────────┘ └─────────┘ └─────────┘ └─────────┘ │
│                                                                          │
│  ┌───────────┐                                                           │
│  │   VM 103  │  Storage:                                                 │
│  │    HAOS   │  ├── /dev/sda (128GB SSD) → pve LVM                       │
│  │    Home   │  ├── /dev/sdb (1TB HDD)  → /mnt/pve/onetb                 │
│  │ Assistant │  └── /dev/sdc (5TB USB)  → /mnt/pve/5tb                   │
│  │  + Webcam │                                                           │
│  │    .142   │                                                           │
│  └───────────┘                                                           │
└──────────────────────────────────────────────────────────────────────────┘
```

## 🔧 Services

| Service | Location | Port | Description |
|---------|----------|------|-------------|
| **Proxmox** | Host | 8006 | Hypervisor management |
| **Filebrowser** | Host | 8085 | Web file manager (5TB ext4) |
| **Tailscale** | Host | - | VPN / remote access |
| **Zapret** | LXC 100 | - | DPI bypass gateway |
| **Jellyfin** | LXC 101 | 8096 | Media server (VAAPI HW transcoding) |
| **qBittorrent** | LXC 102 | 8080 | Torrent client |
| **Radarr** | LXC 102 | 7878 | Movie management |
| **Sonarr** | LXC 102 | 8989 | TV show management |
| **Prowlarr** | LXC 102 | 9696 | Indexer management |
| **Bazarr** | LXC 102 | 6767 | Automatic subtitles (TR + EN) |
| **Jellyseerr** | LXC 102 | 5055 | Netflix-style media request UI |
| **FlareSolverr** | LXC 102 | 8191 | Cloudflare bypass |
| **Homarr** | LXC 102 | 7575 | Unified dashboard |
| **Immich** | LXC 104 | 2283 | Self-hosted Google Photos |
| **Home Assistant** | VM 103 | 8123 | Smart home control (Hue, Keenetic) |
| **go2rtc** | VM 103 | 8554 | Webcam streaming |
| **Apps (Docker)** | LXC 105 | - | General Docker host (contents not inventoried yet) |
| **Gözcü crawler** | LXC 106 | - | Amazon TR crawler (Docker, `pnpm crawler:daemon`) |

## 🖥️ Current Proxmox State

> Read from the Proxmox API on 2026-10-14 (read-only). The step-by-step guide below is how each piece was built; this section is what is actually running now, so check it first when the two differ.

### Host

| Item | Value |
|------|-------|
| **Node** | `pve` (single node) |
| **Proxmox VE** | 9.1.1 |
| **Kernel** | 6.17.2-1-pve |
| **CPU** | Intel Core i7-7700HQ, 1 socket, 4 cores / 8 threads |
| **RAM / swap** | 16GB / 8GB |
| **Network** | `vmbr0` 192.168.1.100/24, gateway 192.168.1.1, bridged on `nic0` (USB Ethernet). `nic1` and `wlp3s0` are unused |
| **DNS** | Tailscale MagicDNS (100.100.100.100) |

### Storage

| Name | Type | Path / backing | Content | Size | Used |
|------|------|----------------|---------|------|------|
| `local` | dir | `/var/lib/vz` | import | 56GB | 7GB (12%) |
| `local-lvm` | LVM-thin | VG `pve`, pool `data` | VM/LXC disks | 58GB | 29GB (50%) |
| `onetb` | dir | `/mnt/pve/onetb` | VM/LXC disks, backups, templates, ISOs, snippets | 983GB | 482GB (49%) |
| `fivetb` | dir | `/mnt/pve/5tb/dump` | backups (keep last 2) | 4.96TB | 1.01TB (20%) |

| Disk | Model | Type | Filesystem | SMART |
|------|-------|------|------------|-------|
| `/dev/sda` | SanDisk X400 M.2 128GB | SSD | Proxmox OS + LVM | PASSED |
| `/dev/sdb` | WDC WD10JPVX 1TB | HDD | ext4 (`onetb`) | PASSED |
| `/dev/sdc` | One Touch 5TB (USB) | USB HDD | ext4 (`/mnt/pve/5tb`) | unknown over USB |

### Guests

All seven guests were running and set to start on boot.

| ID | Type | Name | IP | CPU / RAM / swap | Root disk | Privilege | Start order |
|----|------|------|----|------------------|-----------|-----------|-------------|
| 100 | LXC | `gateway` (Zapret) | 192.168.1.101 | 1 / 512MB / 1GB | 8GB `local-lvm` | privileged | 1 |
| 101 | LXC | `jellyfin` | 192.168.1.102 | 4 / 2GB / 2GB | 30GB `local-lvm` | unprivileged | 2 |
| 102 | LXC | `arr-stack` | 192.168.1.103 | 2 / 3GB / 2GB | 20GB `local-lvm` | unprivileged | 3 |
| 103 | VM | `haos-17.2` | 192.168.1.142 | 2 / 4GB | 32GB `onetb` (q35, OVMF) | n/a | none set |
| 104 | LXC | `immich` | 192.168.1.105 | 4 / 4GB / 2GB | 20GB `local-lvm` | privileged | 5 |
| 105 | LXC | `apps` | 192.168.1.108 | 2 / 2GB / 512MB | 12GB `local-lvm` | unprivileged | none set |
| 106 | LXC | `gozcu-crawler` | 192.168.1.106 (DHCP) | 4 / 4GB / 512MB | 16GB `onetb` | unprivileged | none set |

### Bind mounts and passthrough

| Guest | Host path → guest path |
|-------|------------------------|
| LXC 101 | `/mnt/pve/5tb/media` → `/media` |
| LXC 102 | `/mnt/pve/5tb/media` → `/media`, `/mnt/pve/5tb` → `/storage`, `/mnt/pve/onetb/incomplete-downloads` → `/incomplete` |
| LXC 104 | `/mnt/pve/5tb` → `/storage`, `/mnt/pve/5tb/immich` → `/immich-data` |

- **LXC 101** gets `/dev/dri/card1` and `/dev/dri/renderD129` (Intel iGPU, VAAPI), the NVIDIA device nodes (`/dev/nvidia0`, `nvidiactl`, `nvidia-uvm`, `nvidia-uvm-tools`) and a hookscript, `jellyfin-gpu.sh`.
- **VM 103** gets the USB webcam `0bda:568a`.

### What changed since the last README update

- The 5TB USB drive is now **ext4** (it was exFAT). Media and Immich data now live on it (the old guide had them on the 1TB drive), and a `fivetb` backup storage exists.
- Two new containers: **LXC 105 `apps`** and **LXC 106 `gozcu-crawler`**.
- Memory, swap and disk sizes of LXC 101, 102 and 104 differ from the original `pct create` commands below (current values are in the table above).
- Jellyfin's iGPU render node is now `renderD129` (it was `renderD128`), and the GTX 1050 Ti device nodes are bound in.
- LXC 100 is privileged (`unprivileged: 0`), as its config block below already said; the old diagram said otherwise.
- The host runs Proxmox VE 9.1.1 (kernel 6.17.2).

---

## 📦 Setup Steps

### 1. Proxmox Host Configuration

#### Disable enterprise repos

```bash
sed -i 's/^deb/#deb/' /etc/apt/sources.list.d/pve-enterprise.list
sed -i 's/^deb/#deb/' /etc/apt/sources.list.d/ceph.list
apt update
```

#### IP forwarding

```bash
echo "net.ipv4.ip_forward=1" >> /etc/sysctl.conf
echo "net.ipv4.conf.all.forwarding=1" >> /etc/sysctl.conf
sysctl -p
```

#### Bridge netfilter (for Zapret LXC)

```bash
sysctl -w net.bridge.bridge-nf-call-iptables=1
sysctl -w net.bridge.bridge-nf-call-ip6tables=1
sysctl -w net.bridge.bridge-nf-call-arptables=1
```

#### Disk mounts

```bash
# 1TB HDD - ext4, added via Proxmox GUI (VM 103 disk, LXC 106 root disk, incomplete downloads)
# /mnt/pve/onetb

# 5TB USB HDD - ext4 (it was exFAT before being reformatted), mounted at /mnt/pve/5tb
# Backups go to /mnt/pve/5tb/dump (Proxmox storage "fivetb")

# Media folder structure (5TB)
mkdir -p /mnt/pve/5tb/media/{movies,tv,downloads}
chmod -R 777 /mnt/pve/5tb/media

# Immich storage (5TB, ext4)
mkdir -p /mnt/pve/5tb/immich/{encoded-video,library,thumbs,profile,upload,backups}
chown -R 100000:100000 /mnt/pve/5tb/immich
chmod -R 777 /mnt/pve/5tb/immich
```

#### Filebrowser (on the Host)

> **Update:** the 5TB drive is now ext4 (see Current Proxmox State), so the exFAT limitation below no longer applies. Whether Filebrowser still runs on the host is not visible through the Proxmox API.
>
> **Why on the host?** The exFAT filesystem does not support the Linux permission model. LXC bind mounts cannot grant write access to exFAT — even in a privileged container. Running directly on the host is the only reliable approach.

```bash
curl -fsSL https://raw.githubusercontent.com/filebrowser/get/master/get.sh | bash
mkdir -p /opt/filebrowser
filebrowser config init --database /opt/filebrowser/filebrowser.db
filebrowser config set --address 0.0.0.0 --port 8085 --root /mnt/pve/5tb --database /opt/filebrowser/filebrowser.db
filebrowser users add admin <min-12-char-password> --database /opt/filebrowser/filebrowser.db

cat > /etc/systemd/system/filebrowser.service << 'EOF'
[Unit]
Description=Filebrowser
After=network.target
[Service]
ExecStart=/usr/local/bin/filebrowser --database /opt/filebrowser/filebrowser.db
Restart=always
[Install]
WantedBy=multi-user.target
EOF

systemctl daemon-reload
systemctl enable --now filebrowser
```

---

### 2. LXC 100 — Zapret (DPI Bypass Gateway)

Runs as a gateway LXC. Uses nfqueue + fake packet strategy to bypass DPI blocks in Turkey.

#### IP Forwarding (inside LXC)

```bash
echo "net.ipv4.ip_forward=1" >> /etc/sysctl.conf
sysctl -p
```

#### LXC Config (`/etc/pve/lxc/100.conf`)

```
net0: name=eth0,bridge=vmbr0,firewall=0,ip=192.168.1.101/24,gw=192.168.1.1
features: fuse=1,nesting=1
unprivileged: 0
lxc.apparmor.profile: unconfined
lxc.cgroup.devices.allow: a
lxc.cap.drop:
```

#### Zapret Config (`/opt/zapret/config`)

The most stable parameters for Turkey. Strategy: fake packet + split (1st byte) + md5sig.

```bash
POSTNAT=0
IFACE_LAN=eth0
IFACE_WAN=eth0
NFQWS_OPT="--filter-tcp=443 --filter-udp=443 --dpi-desync=fake,split2 --dpi-desync-split-pos=1 --dpi-desync-fooling=md5sig"
```

#### nftables Rules (`/etc/nftables.conf`)

⚠️ **Critical:** An older version captured all port 443 traffic — this breaks the host's internet because the NFQUEUE handler only runs inside the LXC. The rule below targets **only the LXC IP**:

```bash
table ip zapret_permanent {
    chain catch_prerouting {
        type filter hook prerouting priority -100; policy accept;
        ip saddr 192.168.1.101 tcp dport 443 counter queue num 200
        ip saddr 192.168.1.101 udp dport 443 counter queue num 200
    }
}
```

---

### 3. LXC 101 — Jellyfin (Media Server + iGPU)

#### Create LXC

```bash
pct create 101 local:vztmpl/debian-12-standard_12.12-1_amd64.tar.zst \
  --hostname jellyfin --memory 2048 --swap 2048 --cores 4 \
  --rootfs local-lvm:30 \
  --net0 name=eth0,bridge=vmbr0,ip=192.168.1.102/24,gw=192.168.1.1 \
  --unprivileged 1 --features nesting=1 --start 0
```

#### iGPU Passthrough (`/etc/pve/lxc/101.conf`)

```
hookscript: local:snippets/jellyfin-gpu.sh
lxc.cgroup2.devices.allow: c 226:1 rwm
lxc.cgroup2.devices.allow: c 226:129 rwm
lxc.cgroup2.devices.allow: c 195:* rwm
lxc.cgroup2.devices.allow: c 506:* rwm
lxc.mount.entry: /dev/dri/card1 dev/dri/card1 none bind,optional,create=file
lxc.mount.entry: /dev/dri/renderD129 dev/dri/renderD129 none bind,optional,create=file
lxc.mount.entry: /dev/nvidia0 dev/nvidia0 none bind,optional,create=file
lxc.mount.entry: /dev/nvidiactl dev/nvidiactl none bind,optional,create=file
lxc.mount.entry: /dev/nvidia-uvm dev/nvidia-uvm none bind,optional,create=file
lxc.mount.entry: /dev/nvidia-uvm-tools dev/nvidia-uvm-tools none bind,optional,create=file
```

#### Mount & Install

```bash
pct set 101 -mp0 /mnt/pve/5tb/media,mp=/media

# Inside LXC
apt update && apt install -y curl gnupg
curl -fsSL https://repo.jellyfin.org/install-debuntu.sh | bash
usermod -aG video jellyfin
usermod -aG render jellyfin
systemctl enable --now jellyfin
```

#### VAAPI Transcoding

Dashboard → Playback → Transcoding:
- Hardware acceleration: **VAAPI** → Device: `/dev/dri/renderD129`
- Enable H264, HEVC, MPEG2, VP9, VC1, HEVC 10bit, VP9 10bit

---

### 4. LXC 102 — Arr Stack (Docker)

#### Create LXC

```bash
pct create 102 local:vztmpl/debian-12-standard_12.12-1_amd64.tar.zst \
  --hostname arr-stack --memory 3072 --swap 2048 --cores 2 \
  --rootfs local-lvm:20 \
  --net0 name=eth0,bridge=vmbr0,ip=192.168.1.103/24,gw=192.168.1.1 \
  --unprivileged 1 --features nesting=1 --start 0

pct set 102 -mp0 /mnt/pve/5tb/media,mp=/media
pct set 102 -mp1 /mnt/pve/5tb,mp=/storage
pct set 102 -mp2 /mnt/pve/onetb/incomplete-downloads,mp=/incomplete
```

#### Install Docker

```bash
apt update && apt install -y curl ca-certificates
curl -fsSL https://get.docker.com | sh
cat > /etc/docker/daemon.json << 'EOF'
{"dns": ["1.1.1.1", "8.8.8.8"]}
EOF
systemctl restart docker
```

#### Docker Compose (`/opt/arr/docker-compose.yml`)

```yaml
services:
  qbittorrent:
    image: lscr.io/linuxserver/qbittorrent:latest
    container_name: qbittorrent
    environment:
      - PUID=1000
      - PGID=1000
      - TZ=Europe/Istanbul
      - WEBUI_PORT=8080
    volumes:
      - /opt/arr/qbit-config:/config
      - /media/downloads:/media/downloads
    ports:
      - 8080:8080
    restart: unless-stopped

  prowlarr:
    image: lscr.io/linuxserver/prowlarr:latest
    container_name: prowlarr
    environment:
      - PUID=1000
      - PGID=1000
      - TZ=Europe/Istanbul
    volumes:
      - /opt/arr/prowlarr-config:/config
    ports:
      - 9696:9696
    restart: unless-stopped

  radarr:
    image: lscr.io/linuxserver/radarr:latest
    container_name: radarr
    environment:
      - PUID=1000
      - PGID=1000
      - TZ=Europe/Istanbul
    volumes:
      - /opt/arr/radarr-config:/config
      - /media:/media
    ports:
      - 7878:7878
    restart: unless-stopped

  sonarr:
    image: lscr.io/linuxserver/sonarr:latest
    container_name: sonarr
    environment:
      - PUID=1000
      - PGID=1000
      - TZ=Europe/Istanbul
    volumes:
      - /opt/arr/sonarr-config:/config
      - /media:/media
    ports:
      - 8989:8989
    restart: unless-stopped

  bazarr:
    image: lscr.io/linuxserver/bazarr:latest
    container_name: bazarr
    environment:
      - PUID=1000
      - PGID=1000
      - TZ=Europe/Istanbul
    volumes:
      - /opt/arr/bazarr-config:/config
      - /media:/media
    ports:
      - 6767:6767
    restart: unless-stopped

  flaresolverr:
    image: ghcr.io/flaresolverr/flaresolverr:latest
    container_name: flaresolverr
    environment:
      - TZ=Europe/Istanbul
    ports:
      - 8191:8191
    restart: unless-stopped

  jellyseerr:
    image: fallenbagel/jellyseerr:latest
    container_name: jellyseerr
    environment:
      - TZ=Europe/Istanbul
    volumes:
      - /opt/arr/jellyseerr-config:/app/config
    ports:
      - 5055:5055
    restart: unless-stopped

  homarr:
    image: ghcr.io/homarr-labs/homarr:latest
    container_name: homarr
    environment:
      - TZ=Europe/Istanbul
      - SECRET_ENCRYPTION_KEY=<64-char-hex-key>
      - NODE_TLS_REJECT_UNAUTHORIZED=0
    volumes:
      - /opt/arr/homarr-config:/appdata
    ports:
      - 7575:7575
    restart: unless-stopped
```

#### Service Connection Order

1. **Prowlarr** → Add indexer (1337x + FlareSolverr tag)
2. **Prowlarr → Settings → Apps** → Connect with Radarr/Sonarr API keys
3. **Radarr/Sonarr → Download Clients** → qBittorrent (host: `192.168.1.103`, port: `8080`)
4. **Radarr → Media Management** → Root folder: `/media/movies`
5. **Sonarr → Media Management** → Root folder: `/media/tv`
6. **Bazarr** → Connect Radarr/Sonarr, OpenSubtitles provider, Language profile (EN+TR), assign default profile
7. **Radarr → Profiles** → Remove Remux-1080p/2160p, Quality max 15GB

#### Media Flow

```
Jellyseerr (request) → Radarr/Sonarr → Prowlarr (indexer)
        ↓
  qBittorrent (download) → /media/movies or /media/tv
        ↓
  Bazarr (TR + EN subtitles) → Jellyfin (watch + VAAPI)
```

---

### 5. LXC 104 — Immich (Self-hosted Google Photos)

> **Privileged container** — required so Docker can write to the host mounts.

```bash
pct create 104 local:vztmpl/debian-12-standard_12.12-1_amd64.tar.zst \
  --hostname immich --memory 4096 --swap 2048 --cores 4 \
  --rootfs local-lvm:20 \
  --net0 name=eth0,bridge=vmbr0,ip=192.168.1.105/24,gw=192.168.1.1 \
  --unprivileged 0 --features nesting=1 --start 0

pct set 104 -mp0 /mnt/pve/5tb,mp=/storage
pct set 104 -mp1 /mnt/pve/5tb/immich,mp=/immich-data
```

#### Install (inside LXC)

```bash
echo "nameserver 1.1.1.1" > /etc/resolv.conf
apt update && apt install -y curl ca-certificates
curl -fsSL https://get.docker.com | sh
cat > /etc/docker/daemon.json << 'EOF'
{"dns": ["1.1.1.1", "8.8.8.8"]}
EOF
systemctl restart docker

mkdir -p /opt/immich && cd /opt/immich
wget -O docker-compose.yml https://github.com/immich-app/immich/releases/latest/download/docker-compose.yml
wget -O .env https://github.com/immich-app/immich/releases/latest/download/example.env

sed -i 's|UPLOAD_LOCATION=./library|UPLOAD_LOCATION=/immich-data|' .env
sed -i 's|DB_DATA_LOCATION=./postgres|DB_DATA_LOCATION=/opt/immich/postgres|' .env
sed -i 's|# TZ=Etc/UTC|TZ=Europe/Istanbul|' .env

mkdir -p /opt/immich/postgres
docker compose up -d
```

#### Mobile Backup

iPhone/Android → Immich app → Server: `http://192.168.1.105:2283` → Enable automatic backup

---

### 6. VM 103 — Home Assistant OS

```bash
bash -c "$(wget -qLO - https://raw.githubusercontent.com/community-scripts/ProxmoxVE/main/vm/haos-vm.sh)"

# Webcam passthrough
qm set 103 -usb0 host=0bda:568a
```

Current VM settings: 2 cores, 4GB RAM, 32GB disk on `onetb` (q35, OVMF/UEFI), QEMU guest agent enabled, tag `community-script`.

#### go2rtc (Webcam)

Add-on repo: `https://github.com/AlexxIT/hassio-addons` → Install go2rtc:

```yaml
streams:
  webcam:
    - ffmpeg:device?video=/dev/video0&input_format=mjpeg&video_size=1280x720
```

#### Integrations

- **Philips Hue** — automatic via Hue Bridge
- **Keenetic NDMS2** — presence detection via Telnet
- **Webcam** — go2rtc MJPEG/WebRTC stream

---

### 7. LXC 105 — Apps (Docker)

General-purpose Docker container. What runs inside is not recorded here yet.

```
hostname: apps
cores: 2
memory: 2048
swap: 512
rootfs: local-lvm:vm-105-disk-0,size=12G
net0: name=eth0,bridge=vmbr0,gw=192.168.1.1,ip=192.168.1.108/24,type=veth
nameserver: 1.1.1.1
features: nesting=1,keyctl=1
unprivileged: 1
onboot: 1
```

---

### 8. LXC 106 — Gözcü Crawler (Docker)

Amazon TR crawler (Docker, `pnpm crawler:daemon`), created 2026-09-19 through the Proxmox API. Its root disk lives on the 1TB `onetb` storage and it takes its IP from DHCP (currently 192.168.1.106).

```
hostname: gozcu-crawler
cores: 4
memory: 4096
swap: 512
rootfs: onetb:106/vm-106-disk-0.raw,size=16G
net0: name=eth0,bridge=vmbr0,ip=dhcp,type=veth
features: nesting=1,keyctl=1
unprivileged: 1
onboot: 1
```

---

### 9. Tailscale

```bash
curl -fsSL https://tailscale.com/install.sh | sh
tailscale up --advertise-routes=192.168.1.0/24
```

Approve the subnet route in the admin panel. Installing only on the host is sufficient.

---

### 10. Auto-start

```bash
pct set 100 --onboot 1 --startup order=1   # Zapret
pct set 101 --onboot 1 --startup order=2   # Jellyfin
pct set 102 --onboot 1 --startup order=3   # Arr Stack
pct set 104 --onboot 1 --startup order=5   # Immich

# Start on boot, no explicit order
qm set 103 --onboot 1                      # Home Assistant
pct set 105 --onboot 1                     # Apps
pct set 106 --onboot 1                     # Gözcü crawler
```

---

## 🔍 Troubleshooting

| Problem | Cause | Solution |
|---------|-------|----------|
| Host has no internet | nftables captures all port 443 | Add `ip saddr 192.168.1.101` filter |
| Ethernet at 100Mbps | Cable or negotiation issue | Use Cat5e/Cat6 cable, `ethtool -s nic0 speed 1000` |
| Docker DNS error | Using IPv6 DNS | `daemon.json` → `{"dns":["1.1.1.1","8.8.8.8"]}` |
| Cannot write to LXC mount | Unprivileged container | `chmod 777` from host or use privileged LXC |
| Cannot write to exFAT from LXC/Docker | exFAT has no permission support | Mount with `uid=0,gid=0,dmask=000,fmask=000` on host + run services on host |
| Keenetic blocking internet | MAC policy disabled | Keenetic UI → allow device |
| qBittorrent password keeps changing | Config hash not recognized | `docker logs` → get temp password → set permanent via UI |
| Immich crash loop | `.immich` files missing or unwritable | Create folders from host + use privileged LXC |
| Homarr Proxmox SSL error | Self-signed cert | `NODE_TLS_REJECT_UNAUTHORIZED=0` |
| go2rtc codec error | MJPEG raw format | Add `input_format=mjpeg` to config |
| Radarr downloading 30GB+ files | REMUX profile active | Profiles → remove Remux, Quality max 15GB |
| Bazarr not fetching subtitles | Language profile not assigned | Create default profile (EN+TR), assign to movies |

---

## 📱 Access Table

| Service | URL | Tailscale |
|---------|-----|-----------|
| Proxmox | `https://192.168.1.100:8006` | ✅ |
| Filebrowser | `http://192.168.1.100:8085` | ✅ |
| Jellyfin | `http://192.168.1.102:8096` | ✅ |
| Jellyseerr | `http://192.168.1.103:5055` | ✅ |
| Radarr | `http://192.168.1.103:7878` | ✅ |
| Sonarr | `http://192.168.1.103:8989` | ✅ |
| qBittorrent | `http://192.168.1.103:8080` | ✅ |
| Prowlarr | `http://192.168.1.103:9696` | ✅ |
| Bazarr | `http://192.168.1.103:6767` | ✅ |
| Homarr | `http://192.168.1.103:7575` | ✅ |
| Immich | `http://192.168.1.105:2283` | ✅ |
| Home Assistant | `http://192.168.1.142:8123` | ✅ |

---

## 🔮 Future Plans

- [ ] Nginx Proxy Manager — Reverse proxy + SSL
- [ ] Vaultwarden — Self-hosted password manager
- [ ] Uptime Kuma — Service monitoring
- [ ] Watchtower — Docker auto-update
- [x] Format 5TB to ext4 — permanently resolves exFAT issues
- [ ] Expo-like Android aab/apk builder service

---

## ⚠️ Notes

- This project is for educational purposes
- All access via LAN + Tailscale VPN
- **exFAT (historical):** the 5TB USB disk used to be exFAT, where Linux permissions don't work; it is ext4 now, but the troubleshooting rows about exFAT stay for reference
- **GTX 1050 Ti:** full GPU passthrough is problematic due to Optimus, but its `/dev/nvidia*` device nodes are bound into Jellyfin LXC 101; Ollama is still planned
- **Intel HD 630:** Handles 4K→1080p transcoding comfortably via VAAPI
- Docker IPv6 DNS issue: `daemon.json` DNS override is mandatory in every LXC

*Last updated: October 2026 (Proxmox state read from the API on 2026-10-14)*
