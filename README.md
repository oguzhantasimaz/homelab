# 🏠 Dell 7567 Proxmox Homelab

Eski bir Dell Inspiron 7567 gaming laptop'u tam teşekküllü bir ev sunucusuna dönüştürme rehberi. DPI bypass gateway, medya sunucusu, akıllı ev kontrolü, dosya yönetimi ve uzak erişim tek bir makinede.

Özellikle Türkiye'deki servis sağlayıcıların (Superonline, Türk Telekom vb.) uyguladığı DPI engellerini (Discord, YouTube vb.) aşmak için optimize edilmiş bir Zapret gateway'i içerir.

## 📋 Donanım

| Bileşen | Detay |
|---------|-------|
| **Laptop** | Dell Inspiron 7567 |
| **CPU** | Intel Core i7-7700HQ (4C/8T @ 2.80GHz) |
| **RAM** | 16GB DDR4 |
| **iGPU** | Intel HD Graphics 630 |
| **dGPU** | NVIDIA GTX 1050 Ti Mobile (şu an kullanılmıyor) |
| **SSD** | 128GB (Proxmox OS + LVM) |
| **HDD** | 1TB (medya depolama) |
| **USB HDD** | 5TB (genel depolama / dosya yönetimi) |
| **Ethernet** | USB Ethernet Adaptör (100Mbps) |
| **Router** | Keenetic Titan (PPPoE) |
| **ISP** | Superonline Fiber |

### İstemci Cihazlar

- Windows 11 PC
- iPhone 14 Pro
- MacBook Pro M1 Pro

## 🏗️ Mimari

```
┌─────────────────────────────────────────────────────────┐
│                   Proxmox VE Host                       │
│              192.168.1.100 (vmbr0)                      │
│         Tailscale (subnet router, 192.168.1.0/24)       │
│                                                         │
│  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌───────────┐  │
│  │ LXC 100  │ │ LXC 101  │ │ LXC 102  │ │  VM 103   │  │
│  │ Zapret   │ │ Jellyfin │ │ Arr Stack│ │   HAOS    │  │
│  │ Gateway  │ │  + iGPU  │ │ + Docker │ │  Home     │  │
│  │          │ │  VAAPI   │ │          │ │ Assistant │  │
│  │ .101     │ │ .102     │ │ .103     │ │  .142     │  │
│  └──────────┘ └──────────┘ └──────────┘ └───────────┘  │
│                                                         │
│  Storage:                                               │
│  ├── /dev/sda (128GB SSD) → pve-root + pve-data (LVM)  │
│  ├── /dev/sdb (1TB HDD)  → /mnt/pve/onetb (medya)     │
│  └── /dev/sdc (5TB USB)  → /mnt/pve/5tb (dosyalar)    │
└─────────────────────────────────────────────────────────┘
```

## 🔧 Servisler

| Servis | Konum | Port | Açıklama |
|--------|-------|------|----------|
| **Proxmox** | Host | 8006 | Hypervisor yönetimi |
| **Zapret** | LXC 100 | - | DPI bypass gateway |
| **Jellyfin** | LXC 101 | 8096 | Medya sunucusu (VAAPI HW transcoding) |
| **qBittorrent** | LXC 102 | 8080 | Torrent client |
| **Radarr** | LXC 102 | 7878 | Film yönetimi |
| **Sonarr** | LXC 102 | 8989 | Dizi yönetimi |
| **Prowlarr** | LXC 102 | 9696 | Indexer yönetimi |
| **Bazarr** | LXC 102 | 6767 | Altyazı yönetimi |
| **Jellyseerr** | LXC 102 | 5055 | Medya istek arayüzü |
| **FlareSolverr** | LXC 102 | 8191 | Cloudflare bypass |
| **Homarr** | LXC 102 | 7575 | Dashboard |
| **Filebrowser** | LXC 102 | 8085 | Web dosya yöneticisi |
| **Home Assistant** | VM 103 | 8123 | Akıllı ev kontrolü |
| **go2rtc** | VM 103 | 8554 | Webcam streaming |
| **Tailscale** | Host | - | VPN / uzak erişim |

## 📦 Kurulum Adımları

### 1. Proxmox Host Yapılandırması

#### Enterprise repo'ları devre dışı bırak (lisanssız kullanım)

```bash
sed -i 's/^deb/#deb/' /etc/apt/sources.list.d/pve-enterprise.list
sed -i 's/^deb/#deb/' /etc/apt/sources.list.d/ceph.list
apt update
```

#### IP forwarding aktifle

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
# 1TB HDD (medya)
# Proxmox GUI'den eklenmiş: /mnt/pve/onetb

# 5TB USB HDD
mkdir -p /mnt/pve/5tb
mount /dev/sdc1 /mnt/pve/5tb
echo "/dev/sdc1 /mnt/pve/5tb exfat defaults,nofail 0 0" >> /etc/fstab

# Medya klasör yapısı
mkdir -p /mnt/pve/onetb/media/{movies,tv,downloads}
chmod -R 777 /mnt/pve/onetb/media
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

> **Not:** Eski (hatalı) versiyon `ip saddr` filtresi olmadan tüm trafiği yakalıyordu. Bu durumda host'tan HTTPS bağlantısı kurulamaz.

---

### 3. LXC 101 — Jellyfin (Medya Sunucusu + iGPU)

#### LXC Oluşturma

```bash
pct create 101 local:vztmpl/debian-12-standard_12.12-1_amd64.tar.zst \
  --hostname jellyfin \
  --memory 2048 \
  --swap 512 \
  --cores 4 \
  --rootfs local-lvm:20 \
  --net0 name=eth0,bridge=vmbr0,ip=192.168.1.102/24,gw=192.168.1.1 \
  --unprivileged 1 \
  --features nesting=1 \
  --start 0
```

#### iGPU Passthrough

Intel HD 630 → `card1` + `renderD128` (doğrulama: `ls -l /dev/dri/by-path/`)

LXC config'e ekle (`/etc/pve/lxc/101.conf`):

```
lxc.cgroup2.devices.allow: c 226:1 rwm
lxc.cgroup2.devices.allow: c 226:128 rwm
lxc.mount.entry: /dev/dri/card1 dev/dri/card1 none bind,optional,create=file
lxc.mount.entry: /dev/dri/renderD128 dev/dri/renderD128 none bind,optional,create=file
```

#### Medya Mount

```bash
pct set 101 -mp0 /mnt/pve/onetb/media,mp=/media
```

#### Jellyfin Kurulumu (LXC içinde)

```bash
apt update
apt install -y curl gnupg
curl -fsSL https://repo.jellyfin.org/install-debuntu.sh | bash
usermod -aG video jellyfin
usermod -aG render jellyfin
systemctl enable --now jellyfin
```

#### VAAPI Transcoding Ayarı

Jellyfin Web UI → Dashboard → Playback → Transcoding:
- Hardware acceleration: **VAAPI**
- VA-API Device: `/dev/dri/renderD128`
- H264, HEVC, MPEG2, VP9, VC1, HEVC 10bit, VP9 10bit → hepsini tikle

#### Kütüphane Ekleme

- Movies → `/media/movies`
- TV Shows → `/media/tv`

---

### 4. LXC 102 — Arr Stack (Docker)

#### LXC Oluşturma

```bash
pct create 102 local:vztmpl/debian-12-standard_12.12-1_amd64.tar.zst \
  --hostname arr-stack \
  --memory 2048 \
  --swap 512 \
  --cores 2 \
  --rootfs local-lvm:10 \
  --net0 name=eth0,bridge=vmbr0,ip=192.168.1.103/24,gw=192.168.1.1 \
  --unprivileged 1 \
  --features nesting=1 \
  --start 0
```

#### Mount Points

```bash
pct set 102 -mp0 /mnt/pve/onetb/media,mp=/media
pct set 102 -mp1 /mnt/pve/5tb,mp=/storage
```

#### Docker Kurulumu (LXC içinde)

```bash
apt update
apt install -y curl ca-certificates
curl -fsSL https://get.docker.com | sh

cat > /etc/docker/daemon.json << 'EOF'
{
  "dns": ["1.1.1.1", "8.8.8.8"]
}
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

  filebrowser:
    image: filebrowser/filebrowser:latest
    container_name: filebrowser
    volumes:
      - /storage:/srv
      - /opt/arr/filebrowser-config/filebrowser.db:/database/filebrowser.db
      - /opt/arr/filebrowser-config/settings.json:/config/settings.json
    ports:
      - 8085:80
    restart: unless-stopped
```

#### Başlatma

```bash
cd /opt/arr
docker compose up -d
```

#### Servis Bağlantı Sırası

1. **Prowlarr** → Indexer ekle (1337x + FlareSolverr tag'i)
2. **Prowlarr → Settings → Apps** → Radarr ve Sonarr API key'leriyle bağla
3. **Radarr/Sonarr → Settings → Download Clients** → qBittorrent ekle (host: `192.168.1.103`, port: `8080`)
4. **Radarr → Settings → Media Management** → Root folder: `/media/movies`
5. **Sonarr → Settings → Media Management** → Root folder: `/media/tv`
6. **Bazarr → Settings** → Radarr/Sonarr API key'leriyle bağla, OpenSubtitles provider ekle

#### Medya Akış Şeması

```
Jellyseerr (istek) → Radarr/Sonarr (ara) → Prowlarr (indexer)
                                            ↓
                                      qBittorrent (indir)
                                            ↓
                                    /media/movies veya /media/tv
                                            ↓
                                   Bazarr (altyazı ekle)
                                            ↓
                                   Jellyfin (izle)
```

---

### 5. VM 103 — Home Assistant OS

#### Kurulum

Community script ile HAOS VM oluşturma:

```bash
bash -c "$(wget -qLO - https://raw.githubusercontent.com/community-scripts/ProxmoxVE/main/vm/haos-vm.sh)"
```

Default ayarlar: 4GB RAM, 32GB disk. Kurulum sonrası `http://<VM_IP>:8123` üzerinden erişim.

#### USB Webcam Passthrough

```bash
# Dell 7567 dahili webcam
qm set 103 -usb0 host=0bda:568a
```

#### go2rtc Add-on (Webcam Streaming)

1. HA → Settings → Apps → Add-on Store → Repositories → `https://github.com/AlexxIT/hassio-addons` ekle
2. go2rtc add-on'unu kur
3. Config:

```yaml
streams:
  webcam:
    - ffmpeg:device?video=/dev/video0&input_format=mjpeg&video_size=1280x720
```

4. Dashboard'a iframe kartı olarak ekle

#### Entegrasyonlar

- **Philips Hue** → Otomatik keşfedilir, Hue Bridge üzerinden bağlanır
- **Keenetic NDMS2** → Telnet üzerinden router'a bağlanır (presence detection)
- **Generic Camera** → go2rtc RTSP stream

---

### 6. Tailscale (Uzak Erişim)

#### Host'a Kurulum

```bash
curl -fsSL https://tailscale.com/install.sh | sh
tailscale up --advertise-routes=192.168.1.0/24
```

#### Subnet Route Onaylama

1. login.tailscale.com → Machines → pve
2. Edit route settings → `192.168.1.0/24` enable

#### Mobil Erişim

iPhone/Android'e Tailscale uygulamasını kur, aynı hesapla giriş yap. Tüm `192.168.1.x` servislerine dışarıdan erişebilirsin.

---

### 7. Otomatik Başlatma

```bash
pct set 100 --onboot 1 --startup order=1   # Zapret (önce gateway)
pct set 101 --onboot 1 --startup order=2   # Jellyfin
pct set 102 --onboot 1 --startup order=3   # Arr Stack
qm set 103 --onboot 1 --startup order=4    # Home Assistant
```

---

## 🔍 Troubleshooting

### Host internete çıkamıyor

**Neden:** nftables zapret kuralı tüm 443 trafiğini NFQUEUE'ya atıyor, host'ta handler yok.
**Çözüm:** Kuralı sadece LXC IP'sine (`ip saddr 192.168.1.101`) sınırla.

### Ethernet 100Mbps'te takılı kalıyor

**Neden:** USB ethernet adaptör gigabit destekliyor ama 100Mbps'te negotiate ediyor.
**Çözüm:** Cat5e/Cat6 kablo kullan. `ethtool -s nic0 speed 1000 duplex full autoneg on`

### Docker container'lar DNS çözemiyot

**Neden:** IPv6 DNS kullanmaya çalışıyor.
**Çözüm:** `/etc/docker/daemon.json` → `{"dns": ["1.1.1.1", "8.8.8.8"]}`

### LXC'de chown çalışmıyor (mount point)

**Neden:** Unprivileged container'da mount edilen dizinlerde ownership değiştirilemez.
**Çözüm:** PVE host'tan `chmod -R 777 /mnt/pve/onetb/media`

### Keenetic internet policy engelliyor

**Neden:** Keenetic'te yeni MAC adresleri için internet erişim policy'si kapalı olabilir.
**Çözüm:** Keenetic web UI → Connection policy → ilgili cihaza izin ver.

### qBittorrent her restart'ta şifre değişiyor

**Neden:** Config dosyasındaki password hash formatı tanınmıyor.
**Çözüm:** Logdan temp şifreyi al (`docker logs qbittorrent | grep "temporary password"`), hemen giriş yap ve UI'dan kalıcı şifre belirle.

---

## 📱 Erişim Tablosu

| Servis | LAN URL | Tailscale ile Dışarıdan |
|--------|---------|------------------------|
| Proxmox | `https://192.168.1.100:8006` | ✅ |
| Jellyfin | `http://192.168.1.102:8096` | ✅ |
| Jellyseerr | `http://192.168.1.103:5055` | ✅ |
| Radarr | `http://192.168.1.103:7878` | ✅ |
| Sonarr | `http://192.168.1.103:8989` | ✅ |
| qBittorrent | `http://192.168.1.103:8080` | ✅ |
| Prowlarr | `http://192.168.1.103:9696` | ✅ |
| Bazarr | `http://192.168.1.103:6767` | ✅ |
| Homarr | `http://192.168.1.103:7575` | ✅ |
| Filebrowser | `http://192.168.1.103:8085` | ✅ |
| Home Assistant | `http://192.168.1.142:8123` | ✅ |

---

## 🔮 Gelecek Planlar

- [ ] **Immich** — Self-hosted Google Photos alternatifi
- [ ] **Nginx Proxy Manager** — Reverse proxy + SSL
- [ ] **Vaultwarden** — Self-hosted şifre yöneticisi
- [ ] **Uptime Kuma** — Servis monitoring
- [ ] **Watchtower** — Docker auto-update

---

## 📝 Notlar

- Bu proje eğitim amaçlıdır ve ağ güvenliği prensiplerini anlamak için oluşturulmuştur
- Tüm servisler LAN içinde çalışır, dışarıdan erişim sadece Tailscale VPN üzerinden sağlanır
- GTX 1050 Ti şu an kullanılmıyor — laptop Optimus mimarisi nedeniyle GPU passthrough sorunlu, ileride Ollama için değerlendirilebilir
- Intel HD 630 iGPU VAAPI ile Jellyfin hardware transcoding 4K→1080p dahil rahat kaldırır

---

*Son güncelleme: Nisan 2026*
