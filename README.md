# Homelab Proxmox-Zapret-Gateway

Bu proje, bir Proxmox LXC konteyneri üzerinde **Zapret** (DPI Bypass) kullanarak ev ağındaki tüm cihazlar için (Windows, iOS, Android vb.) şeffaf bir sansür aşma ağ geçidi (Gateway) oluşturmayı hedefler. 

Özellikle Türkiye'deki servis sağlayıcıların (Superonline, Türk Telekom vb.) uyguladığı sert DPI engellerini (Discord, YouTube vb.) aşmak için optimize edilmiştir.

---

## 🛠️ Donanım ve Ortam
* **Anamakine:** Dell Laptop (Proxmox VE)
* **Gateway:** Debian/Ubuntu LXC Container (ID: 100)
* **İstemciler:** Windows 11 PC, iPhone 14 Pro, Macbook Pro M1 Pro  
* **İnternet:** 1 Gbps Fiber (DPI Müdahaleli)

---

## 🏗️ 1. Proxmox Host Yapılandırması

LXC'nin ağ trafiğini manipüle edebilmesi için host seviyesinde bazı kısıtlamaların kaldırılması gerekir.

### Bridge Netfilter Aktivasyonu
Host terminalinde şu komutları çalıştırın:
```bash
sysctl -w net.bridge.bridge-nf-call-iptables=1
sysctl -w net.bridge.bridge-nf-call-ip6tables=1
sysctl -w net.bridge.bridge-nf-call-arptables=1
```


Konteyner Ayrıcalıkları (/etc/pve/lxc/100.conf)

Konteynerin ağ kartına tam erişimi için konfigürasyona şu satırları ekleyin:

```bash
net0: name=eth0,bridge=vmbr0,firewall=0,ip=192.168.1.101/24,gw=192.168.1.1
features: fuse=1,nesting=1
unprivileged: 0
lxc.apparmor.profile: unconfined
lxc.cgroup.devices.allow: a
lxc.cap.drop:
```

## 🔌 2. Gateway LXC Yapılandırması

```bash
echo "net.ipv4.ip_forward=1" >> /etc/sysctl.conf
sysctl -p
```

Zapret Kurulumu ve Altın Ayarlar
/opt/zapret/config dosyasında Türkiye için çalışan en stabil parametreler:

```bash
POSTNAT=0
IFACE_LAN=eth0
IFACE_WAN=eth0

# En stabil strateji: fake paket + split (1. byte) + md5sig
NFQWS_OPT="--filter-tcp=443 --filter-udp=443 --dpi-desync=fake,split2 --dpi-desync-split-pos=1 --dpi-desync-fooling=md5sig"
```

Nftables Kalıcı Kurallar (/etc/nftables.conf)
Paketlerin "Forward" aşamasında kaçmaması için "Prerouting" kancası ile yakalıyoruz:

```bash
table ip zapret_permanent {
    chain catch_prerouting {
        type filter hook prerouting priority -100; policy accept;
        tcp dport 443 counter queue num 200
        udp dport 443 counter queue num 200
    }
}
```





