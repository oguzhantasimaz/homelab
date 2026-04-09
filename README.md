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
| **dGPU** | NVIDIA GTX 1050 Ti Mobile (future Ollama use) |
| **Webcam** | Realtek Integrated Webcam (0bda:568a) |
| **SSD** | 128GB (Proxmox OS + LVM) |
| **HDD** | 1TB ext4 (media + Immich storage) |
| **USB HDD** | 5TB exFAT (general storage / file management) |
| **Ethernet** | USB Ethernet Adapter (100Mbps negotiated) |
| **Router** | Keenetic Titan (PPPoE) |
| **ISP** | Superonline Fiber |

### Client Devices

- Windows 11 PC
- iPhone 14 Pro
- MacBook Pro M1 Pro

## 🏗️ Architecture

```
┌──────────────────────────────────────────────────────────────┐
│                     Proxmox VE Host                          │
│                192.168.1.100 (vmbr0)                         │
│           Tailscale (subnet router, 192.168.1.0/24)          │
│           Filebrowser (:8085 → 5TB exFAT)                    │
│                                                              │
│  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌────────────────┐  │
│  │ LXC 100  │ │ LXC 101  │ │ LXC 102  │ │ LXC 104 (priv) │  │
│  │ Zapret   │ │ Jellyfin │ │ Arr Stack│ │    Immich       │  │
│  │ Gateway  │ │  + iGPU  │ │ + Docker │ │  + Photo        │  │
│  │ unpriv   │ │  VAAPI   │ │          │ │    Backup       │  │
│  │ .101     │ │ .102     │ │ .103     │ │    .105         │  │
│  └──────────┘ └──────────┘ └──────────┘ └────────────────┘  │
│                                                              │
│  ┌───────────┐                                               │
│  │  VM 103   │  Storage:                                     │
│  │   HAOS    │  ├── /dev/sda (128GB SSD) → pve LVM           │
│  │  Home     │  ├── /dev/sdb (1TB HDD)  → /mnt/pve/onetb    │
│  │ Assistant │  └── /dev/sdc (5TB USB)  → /mnt/pve/5tb      │
│  │  + Webcam │                                               │
│  │  .142     │                                               │
│  └───────────┘                                               │
└──────────────────────────────────────────────────────────────┘
```

## 🔧 Services

| Service | Location | Port | Description |
|---------|----------|------|-------------|
| **Proxmox** | Host | 8006 | Hypervisor management |
| **Filebrowser** | Host | 8085 | Web file manager (5TB exFAT) |
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
# 1TB HDD (media) - ext4, added via Proxmox GUI
# /mnt/pve/onetb

# 5TB USB HDD (exFAT — requires custom mount)
mkdir -p /mnt/pve/5tb
mount -t exfat -o rw,uid=0,gid=0,dmask=000,fmask=000 /dev/sdc1 /mnt/pve/5tb
echo "/dev/sdc1 /mnt/pve/5tb exfat rw,uid=0,gid=0,dmask=000,fmask=000,nofail 0 0" >> /etc/fstab

# Media folder structure
mkdir -p /mnt/pve/onetb/media/{movies,tv,downloads}
chmod -R 777 /mnt/pve/onetb/media

# Immich storage (1TB HDD, ext4)
mkdir -p /mnt/pve/onetb/immich/{encoded-video,library,thumbs,profile,upload,backups}
chown -R 100000:100000 /mnt/pve/onetb/immich
chmod -R 777 /mnt/pve/onetb/immich
```

#### Filebrowser (on the Host)

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
  --hostname jellyfin --memory 2048 --swap 512 --cores 4 \
  --rootfs local-lvm:20 \
  --net0 name=eth0,bridge=vmbr0,ip=192.168.1.102/24,gw=192.168.1.1 \
  --unprivileged 1 --features nesting=1 --start 0
```

#### iGPU Passthrough (`/etc/pve/lxc/101.conf`)

```
lxc.cgroup2.devices.allow: c 226:1 rwm
lxc.cgroup2.devices.allow: c 226:128 rwm
lxc.mount.entry: /dev/dri/card1 dev/dri/card1 none bind,optional,create=file
lxc.mount.entry: /dev/dri/renderD128 dev/dri/renderD128 none bind,optional,create=file
```

#### Mount & Install

```bash
pct set 101 -mp0 /mnt/pve/onetb/media,mp=/media

# Inside LXC
apt update && apt install -y curl gnupg
curl -fsSL https://repo.jellyfin.org/install-debuntu.sh | bash
usermod -aG video jellyfin
usermod -aG render jellyfin
systemctl enable --now jellyfin
```

#### VAAPI Transcoding

Dashboard → Playback → Transcoding:
- Hardware acceleration: **VAAPI** → Device: `/dev/dri/renderD128`
- Enable H264, HEVC, MPEG2, VP9, VC1, HEVC 10bit, VP9 10bit

---

### 4. LXC 102 — Arr Stack (Docker)

#### Create LXC

```bash
pct create 102 local:vztmpl/debian-12-standard_12.12-1_amd64.tar.zst \
  --hostname arr-stack --memory 2048 --swap 512 --cores 2 \
  --rootfs local-lvm:10 \
  --net0 name=eth0,bridge=vmbr0,ip=192.168.1.103/24,gw=192.168.1.1 \
  --unprivileged 1 --features nesting=1 --start 0

pct set 102 -mp0 /mnt/pve/onetb/media,mp=/media
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

> **Privileged container** — required so Docker can write to the 1TB HDD mount.

```bash
pct create 104 local:vztmpl/debian-12-standard_12.12-1_amd64.tar.zst \
  --hostname immich --memory 4096 --swap 1024 --cores 4 \
  --rootfs local-lvm:20 \
  --net0 name=eth0,bridge=vmbr0,ip=192.168.1.105/24,gw=192.168.1.1 \
  --unprivileged 0 --features nesting=1 --start 0

pct set 104 -mp0 /mnt/pve/5tb,mp=/storage
pct set 104 -mp1 /mnt/pve/onetb/immich,mp=/immich-data
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

### 7. Tailscale

```bash
curl -fsSL https://tailscale.com/install.sh | sh
tailscale up --advertise-routes=192.168.1.0/24
```

Approve the subnet route in the admin panel. Installing only on the host is sufficient.

---

### 8. Auto-start

```bash
pct set 100 --onboot 1 --startup order=1   # Zapret
pct set 101 --onboot 1 --startup order=2   # Jellyfin
pct set 102 --onboot 1 --startup order=3   # Arr Stack
qm set 103 --onboot 1 --startup order=4    # Home Assistant
pct set 104 --onboot 1 --startup order=5   # Immich
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
- [ ] Format 5TB to ext4 — permanently resolves exFAT issues
- [ ] Expo-like Android aab/apk builder service

---

## ⚠️ Notes

- This project is for educational purposes
- All access via LAN + Tailscale VPN
- **exFAT:** 5TB USB disk — Linux permissions don't work; services that need write access must run on the host
- **GTX 1050 Ti:** GPU passthrough problematic due to Optimus; reserved for future Ollama use
- **Intel HD 630:** Handles 4K→1080p transcoding comfortably via VAAPI
- Docker IPv6 DNS issue: `daemon.json` DNS override is mandatory in every LXC

*Last updated: April 2026*
