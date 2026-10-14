# 🏠 Dell 7567 Proxmox Homelab

> 🌐 [English](README.md) | **Türkçe**

Eski bir Dell Inspiron 7567 gaming laptop'u tam teşekküllü bir ev sunucusuna dönüştürme rehberi. DPI bypass gateway, medya sunucusu, akıllı ev kontrolü, fotoğraf yedekleme, dosya yönetimi ve uzak erişim tek bir makinede.

Özellikle Türkiye'deki servis sağlayıcıların (Superonline, Türk Telekom vb.) uyguladığı DPI engellerini (Discord, YouTube vb.) aşmak için optimize edilmiş bir Zapret gateway'i içerir.

## 📋 Donanım

| Bileşen | Detay |
|---------|-------|
| **Laptop** | Dell Inspiron 7567 |
| **CPU** | Intel Core i7-7700HQ (4C/8T @ 2.80GHz) |
| **RAM** | 16GB DDR4 |
| **iGPU** | Intel HD Graphics 630 (Jellyfin VAAPI) |
| **dGPU** | NVIDIA GTX 1050 Ti Mobile (device node'ları Jellyfin LXC 101'e bağlı; Ollama planlı) |
| **Webcam** | Realtek Integrated Webcam (0bda:568a) |
| **SSD** | 128GB SanDisk X400 (Proxmox OS + LVM) |
| **HDD** | 1TB ext4 (VM/LXC diskleri, tamamlanmamış indirmeler) |
| **USB HDD** | 5TB ext4 (medya, Immich, yedekler, genel depolama) |
| **Ethernet** | USB Ethernet Adaptör (100Mbps negotiated) |
| **Hypervisor** | Proxmox VE 9.1.1 (kernel 6.17.2-1-pve) |
| **Router** | Keenetic Titan (PPPoE) |
| **ISP** | Superonline Fiber |

### İstemci Cihazlar

- Windows 11 PC
- iPhone 14 Pro
- MacBook Pro M1 Pro

## 🏗️ Mimari

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
│  │ Gateway │ │  + GPU  │ │ + Docker│ │+ Fotoğraf│ │ + Docker│ │ crawler ││
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

## 🔧 Servisler

| Servis | Konum | Port | Açıklama |
|--------|-------|------|----------|
| **Proxmox** | Host | 8006 | Hypervisor yönetimi |
| **Filebrowser** | Host | 8085 | Web dosya yöneticisi (5TB ext4) |
| **Tailscale** | Host | - | VPN / uzak erişim |
| **Zapret** | LXC 100 | - | DPI bypass gateway |
| **Jellyfin** | LXC 101 | 8096 | Medya sunucusu (VAAPI HW transcoding) |
| **qBittorrent** | LXC 102 | 8080 | Torrent client |
| **Radarr** | LXC 102 | 7878 | Film yönetimi |
| **Sonarr** | LXC 102 | 8989 | Dizi yönetimi |
| **Prowlarr** | LXC 102 | 9696 | Indexer yönetimi |
| **Bazarr** | LXC 102 | 6767 | Otomatik altyazı (TR + EN) |
| **Jellyseerr** | LXC 102 | 5055 | Netflix tarzı medya istek arayüzü |
| **FlareSolverr** | LXC 102 | 8191 | Cloudflare bypass |
| **Homarr** | LXC 102 | 7575 | Unified dashboard |
| **Immich** | LXC 104 | 2283 | Self-hosted Google Photos |
| **Home Assistant** | VM 103 | 8123 | Akıllı ev kontrolü (Hue, Keenetic) |
| **go2rtc** | VM 103 | 8554 | Webcam streaming |
| **Apps (Docker)** | LXC 105 | - | Genel Docker host'u (içeriği henüz envantere alınmadı) |
| **Gözcü crawler** | LXC 106 | - | Amazon TR crawler (Docker, `pnpm crawler:daemon`) |

## 🖥️ Güncel Proxmox Durumu

> 2026-10-14 tarihinde Proxmox API'sinden okundu (salt okunur). Aşağıdaki adım adım rehber her parçanın nasıl kurulduğunu anlatır; bu bölüm ise şu anda gerçekte çalışanı gösterir. İkisi farklıysa önce bu bölüme bak.

### Host

| Öğe | Değer |
|-----|-------|
| **Node** | `pve` (tek node) |
| **Proxmox VE** | 9.1.1 |
| **Kernel** | 6.17.2-1-pve |
| **CPU** | Intel Core i7-7700HQ, 1 soket, 4 çekirdek / 8 thread |
| **RAM / swap** | 16GB / 8GB |
| **Ağ** | `vmbr0` 192.168.1.100/24, gateway 192.168.1.1, `nic0` (USB Ethernet) üzerinde bridge. `nic1` ve `wlp3s0` kullanılmıyor |
| **DNS** | Tailscale MagicDNS (100.100.100.100) |

### Depolama

| Ad | Tür | Yol / arka uç | İçerik | Boyut | Kullanılan |
|----|-----|---------------|--------|-------|------------|
| `local` | dir | `/var/lib/vz` | import | 56GB | 7GB (%12) |
| `local-lvm` | LVM-thin | VG `pve`, pool `data` | VM/LXC diskleri | 58GB | 29GB (%50) |
| `onetb` | dir | `/mnt/pve/onetb` | VM/LXC diskleri, yedekler, şablonlar, ISO'lar, snippet'ler | 983GB | 482GB (%49) |
| `fivetb` | dir | `/mnt/pve/5tb/dump` | yedekler (son 2 tutulur) | 4.96TB | 1.01TB (%20) |

| Disk | Model | Tür | Dosya sistemi | SMART |
|------|-------|-----|---------------|-------|
| `/dev/sda` | SanDisk X400 M.2 128GB | SSD | Proxmox OS + LVM | PASSED |
| `/dev/sdb` | WDC WD10JPVX 1TB | HDD | ext4 (`onetb`) | PASSED |
| `/dev/sdc` | One Touch 5TB (USB) | USB HDD | ext4 (`/mnt/pve/5tb`) | USB üzerinden bilinmiyor |

### Guest'ler

Yedi guest'in hepsi çalışıyordu ve boot'ta başlayacak şekilde ayarlıydı.

| ID | Tür | Ad | IP | CPU / RAM / swap | Root disk | Yetki | Başlatma sırası |
|----|-----|----|----|------------------|-----------|-------|-----------------|
| 100 | LXC | `gateway` (Zapret) | 192.168.1.101 | 1 / 512MB / 1GB | 8GB `local-lvm` | privileged | 1 |
| 101 | LXC | `jellyfin` | 192.168.1.102 | 4 / 2GB / 2GB | 30GB `local-lvm` | unprivileged | 2 |
| 102 | LXC | `arr-stack` | 192.168.1.103 | 2 / 3GB / 2GB | 20GB `local-lvm` | unprivileged | 3 |
| 103 | VM | `haos-17.2` | 192.168.1.142 | 2 / 4GB | 32GB `onetb` (q35, OVMF) | - | ayarlı değil |
| 104 | LXC | `immich` | 192.168.1.105 | 4 / 4GB / 2GB | 20GB `local-lvm` | privileged | 5 |
| 105 | LXC | `apps` | 192.168.1.108 | 2 / 2GB / 512MB | 12GB `local-lvm` | unprivileged | ayarlı değil |
| 106 | LXC | `gozcu-crawler` | 192.168.1.106 (DHCP) | 4 / 4GB / 512MB | 16GB `onetb` | unprivileged | ayarlı değil |

### Bind mount'lar ve passthrough

| Guest | Host yolu → guest yolu |
|-------|------------------------|
| LXC 101 | `/mnt/pve/5tb/media` → `/media` |
| LXC 102 | `/mnt/pve/5tb/media` → `/media`, `/mnt/pve/5tb` → `/storage`, `/mnt/pve/onetb/incomplete-downloads` → `/incomplete` |
| LXC 104 | `/mnt/pve/5tb` → `/storage`, `/mnt/pve/5tb/immich` → `/immich-data` |

- **LXC 101**: `/dev/dri/card1` ve `/dev/dri/renderD129` (Intel iGPU, VAAPI), NVIDIA device node'ları (`/dev/nvidia0`, `nvidiactl`, `nvidia-uvm`, `nvidia-uvm-tools`) ve `jellyfin-gpu.sh` hookscript'i.
- **VM 103**: USB webcam `0bda:568a`.

### Son README güncellemesinden beri değişenler

- 5TB USB disk artık **ext4** (eskiden exFAT'tı). Medya ve Immich verisi artık burada (eski rehberde 1TB diskteydi) ve `fivetb` yedek depolaması mevcut.
- İki yeni container: **LXC 105 `apps`** ve **LXC 106 `gozcu-crawler`**.
- LXC 101, 102 ve 104'ün bellek, swap ve disk boyutları aşağıdaki orijinal `pct create` komutlarından farklı (güncel değerler yukarıdaki tabloda).
- Jellyfin'in iGPU render node'u artık `renderD129` (eskiden `renderD128`), ayrıca GTX 1050 Ti device node'ları bağlı.
- LXC 100 privileged (`unprivileged: 0`); aşağıdaki config bloğu zaten böyle diyordu, eski diyagram yanlıştı.
- Host Proxmox VE 9.1.1 (kernel 6.17.2) çalıştırıyor.

---

## 📦 Kurulum Adımları

### 1. Proxmox Host Yapılandırması

#### Enterprise repo'ları devre dışı bırak

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

#### Bridge netfilter (Zapret LXC için)

```bash
sysctl -w net.bridge.bridge-nf-call-iptables=1
sysctl -w net.bridge.bridge-nf-call-ip6tables=1
sysctl -w net.bridge.bridge-nf-call-arptables=1
```

#### Disk mount'ları

```bash
# 1TB HDD - ext4, Proxmox GUI'den eklenmiş (VM 103 diski, LXC 106 root diski, tamamlanmamış indirmeler)
# /mnt/pve/onetb

# 5TB USB HDD - ext4 (yeniden formatlanmadan önce exFAT'tı), /mnt/pve/5tb'ye mount'lu
# Yedekler /mnt/pve/5tb/dump'a gider (Proxmox depolaması "fivetb")

# Medya klasör yapısı (5TB)
mkdir -p /mnt/pve/5tb/media/{movies,tv,downloads}
chmod -R 777 /mnt/pve/5tb/media

# Immich depolama (5TB, ext4)
mkdir -p /mnt/pve/5tb/immich/{encoded-video,library,thumbs,profile,upload,backups}
chown -R 100000:100000 /mnt/pve/5tb/immich
chmod -R 777 /mnt/pve/5tb/immich
```

#### Filebrowser (Host üzerinde)

> **Güncelleme:** 5TB disk artık ext4 (bkz. Güncel Proxmox Durumu), bu yüzden aşağıdaki exFAT kısıtı artık geçerli değil. Filebrowser'ın hâlâ host'ta çalışıp çalışmadığı Proxmox API'sinden görünmüyor.
>
> **Neden host'ta?** exFAT dosya sistemi Linux permission modelini desteklemez. LXC bind mount'ları exFAT'a yazma izni veremez — privileged container'da bile. Host'ta direkt çalıştırmak tek güvenilir yol.

```bash
curl -fsSL https://raw.githubusercontent.com/filebrowser/get/master/get.sh | bash
mkdir -p /opt/filebrowser
filebrowser config init --database /opt/filebrowser/filebrowser.db
filebrowser config set --address 0.0.0.0 --port 8085 --root /mnt/pve/5tb --database /opt/filebrowser/filebrowser.db
filebrowser users add admin <min-12-karakter-sifre> --database /opt/filebrowser/filebrowser.db

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

Gateway LXC olarak çalışır. Türkiye'deki DPI engellerini aşmak için nfqueue + fake packet stratejisi kullanır.

#### IP Forwarding (LXC içinde)

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

Türkiye için çalışan en stabil parametreler. Strateji: fake paket + split (1. byte) + md5sig.

```bash
POSTNAT=0
IFACE_LAN=eth0
IFACE_WAN=eth0
NFQWS_OPT="--filter-tcp=443 --filter-udp=443 --dpi-desync=fake,split2 --dpi-desync-split-pos=1 --dpi-desync-fooling=md5sig"
```

#### nftables Kuralları (`/etc/nftables.conf`)

⚠️ **Kritik:** Eski versiyonda tüm 443 trafiği yakalanıyordu — bu host'un internetini keser çünkü NFQUEUE handler sadece LXC içinde çalışır. Aşağıdaki kural **sadece LXC IP'sini** hedefler:

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

### 3. LXC 101 — Jellyfin (Medya Sunucusu + iGPU)

#### LXC Oluşturma

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

#### Mount & Kurulum

```bash
pct set 101 -mp0 /mnt/pve/5tb/media,mp=/media

# LXC içinde
apt update && apt install -y curl gnupg
curl -fsSL https://repo.jellyfin.org/install-debuntu.sh | bash
usermod -aG video jellyfin
usermod -aG render jellyfin
systemctl enable --now jellyfin
```

#### VAAPI Transcoding

Dashboard → Playback → Transcoding:
- Hardware acceleration: **VAAPI** → Device: `/dev/dri/renderD129`
- H264, HEVC, MPEG2, VP9, VC1, HEVC 10bit, VP9 10bit hepsini aktifle

---

### 4. LXC 102 — Arr Stack (Docker)

#### LXC Oluşturma

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

#### Docker Kurulumu

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

#### Servis Bağlantı Sırası

1. **Prowlarr** → Indexer ekle (1337x + FlareSolverr tag'i)
2. **Prowlarr → Settings → Apps** → Radarr/Sonarr API key'leriyle bağla
3. **Radarr/Sonarr → Download Clients** → qBittorrent (host: `192.168.1.103`, port: `8080`)
4. **Radarr → Media Management** → Root folder: `/media/movies`
5. **Sonarr → Media Management** → Root folder: `/media/tv`
6. **Bazarr** → Radarr/Sonarr bağla, OpenSubtitles provider, Language profile (EN+TR), default profile ata
7. **Radarr → Profiles** → Remux-1080p/2160p kaldır, Quality max 15GB

#### Medya Akışı

```
Jellyseerr (istek) → Radarr/Sonarr → Prowlarr (indexer)
        ↓
  qBittorrent (indir) → /media/movies veya /media/tv
        ↓
  Bazarr (TR + EN altyazı) → Jellyfin (izle + VAAPI)
```

---

### 5. LXC 104 — Immich (Self-hosted Google Photos)

> **Privileged container** — Docker'ın host mount'larına yazabilmesi için zorunlu.

```bash
pct create 104 local:vztmpl/debian-12-standard_12.12-1_amd64.tar.zst \
  --hostname immich --memory 4096 --swap 2048 --cores 4 \
  --rootfs local-lvm:20 \
  --net0 name=eth0,bridge=vmbr0,ip=192.168.1.105/24,gw=192.168.1.1 \
  --unprivileged 0 --features nesting=1 --start 0

pct set 104 -mp0 /mnt/pve/5tb,mp=/storage
pct set 104 -mp1 /mnt/pve/5tb/immich,mp=/immich-data
```

#### Kurulum (LXC içinde)

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

#### Mobil Yedekleme

iPhone/Android → Immich uygulaması → Server: `http://192.168.1.105:2283` → Otomatik yedekleme aç

---

### 6. VM 103 — Home Assistant OS

```bash
bash -c "$(wget -qLO - https://raw.githubusercontent.com/community-scripts/ProxmoxVE/main/vm/haos-vm.sh)"

# Webcam passthrough
qm set 103 -usb0 host=0bda:568a
```

Güncel VM ayarları: 2 çekirdek, 4GB RAM, `onetb` üzerinde 32GB disk (q35, OVMF/UEFI), QEMU guest agent açık, tag `community-script`.

#### go2rtc (Webcam)

Add-on repo: `https://github.com/AlexxIT/hassio-addons` → go2rtc kur:

```yaml
streams:
  webcam:
    - ffmpeg:device?video=/dev/video0&input_format=mjpeg&video_size=1280x720
```

#### Entegrasyonlar

- **Philips Hue** — Hue Bridge üzerinden otomatik
- **Keenetic NDMS2** — Telnet ile presence detection
- **Webcam** — go2rtc MJPEG/WebRTC stream

---

### 7. LXC 105 — Apps (Docker)

Genel amaçlı Docker container'ı. İçinde ne çalıştığı henüz burada kayıtlı değil.

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

Amazon TR crawler'ı (Docker, `pnpm crawler:daemon`), 2026-09-19'da Proxmox API ile oluşturuldu. Root diski 1TB `onetb` depolamasında, IP'yi DHCP'den alıyor (şu an 192.168.1.106).

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

Admin panelinde subnet route approve et. Sadece host'a kurmak yeterli.

---

### 10. Otomatik Başlatma

```bash
pct set 100 --onboot 1 --startup order=1   # Zapret
pct set 101 --onboot 1 --startup order=2   # Jellyfin
pct set 102 --onboot 1 --startup order=3   # Arr Stack
pct set 104 --onboot 1 --startup order=5   # Immich

# Boot'ta başlar, açık sıra yok
qm set 103 --onboot 1                      # Home Assistant
pct set 105 --onboot 1                     # Apps
pct set 106 --onboot 1                     # Gözcü crawler
```

---

## 🔍 Troubleshooting

| Sorun | Neden | Çözüm |
|-------|-------|-------|
| Host internete çıkamıyor | nftables tüm 443'ü yakalıyor | `ip saddr 192.168.1.101` filtresi ekle |
| Ethernet 100Mbps | Kablo veya negotiation | Cat5e/Cat6 kablo, `ethtool -s nic0 speed 1000` |
| Docker DNS hatası | IPv6 DNS kullanıyor | `daemon.json` → `{"dns":["1.1.1.1","8.8.8.8"]}` |
| LXC'de mount'a yazılamıyor | Unprivileged container | Host'tan `chmod 777` veya privileged LXC |
| exFAT'a LXC/Docker yazamıyor | exFAT permission desteklemez | Host'ta `uid=0,gid=0,dmask=000,fmask=000` mount + servisleri host'ta çalıştır |
| Keenetic internet engelliyor | MAC policy kapalı | Keenetic UI → cihaza izin ver |
| qBittorrent şifre değişiyor | Config hash tanınmıyor | `docker logs` → temp şifre → UI'dan kalıcı belirle |
| Immich crash loop | `.immich` dosyaları eksik/yazılamıyor | Host'tan klasör oluştur + privileged LXC |
| Homarr Proxmox SSL hatası | Self-signed cert | `NODE_TLS_REJECT_UNAUTHORIZED=0` |
| go2rtc codec hatası | MJPEG raw format | Config'e `input_format=mjpeg` ekle |
| Radarr 30GB+ dosya | REMUX profili aktif | Profiles → Remux kaldır, Quality max 15GB |
| Bazarr altyazı getirmiyor | Language profile atanmamış | Default profile oluştur (EN+TR), filmlere ata |

---

## 📱 Erişim Tablosu

| Servis | URL | Tailscale |
|--------|-----|-----------|
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

## 🔮 Gelecek Planlar

- [ ] Nginx Proxy Manager — Reverse proxy + SSL
- [ ] Vaultwarden — Self-hosted şifre yöneticisi
- [ ] Uptime Kuma — Servis monitoring
- [ ] Watchtower — Docker auto-update
- [x] 5TB diski ext4'e format — exFAT sorunlarını kalıcı çözer
- [ ] Expo benzeri android aab/apk builder servisi

---

## ⚠️ Notlar

- Bu proje eğitim amaçlıdır
- Tüm erişim LAN + Tailscale VPN üzerinden
- **exFAT (geçmiş):** 5TB USB disk eskiden exFAT'tı ve Linux permission çalışmıyordu; artık ext4, exFAT ile ilgili sorun giderme satırları referans için duruyor
- **GTX 1050 Ti:** Optimus nedeniyle tam GPU passthrough sorunlu, ama `/dev/nvidia*` device node'ları Jellyfin LXC 101'e bağlı; Ollama hâlâ planlı
- **Intel HD 630:** VAAPI ile 4K→1080p transcoding rahat kaldırır
- Docker IPv6 DNS sorunu: her LXC'de `daemon.json` ile DNS zorunlu

*Son güncelleme: Ekim 2026 (Proxmox durumu 2026-10-14'te API'den okundu)*
