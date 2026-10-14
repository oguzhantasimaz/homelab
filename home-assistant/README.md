# Home Assistant dashboard

Redesigned "Ev" dashboard (7 views, sections layout) for the HAOS VM described in the main README.
This repo is public: **no tokens, URLs or private entity data belong here.**

The config is not stored in git by Home Assistant itself, so this is a ready-to-paste design.
All entity IDs are placeholders (marked `# EDIT`) because HA is only reachable from the home network.

## Apply

1. HACS > Frontend: install **mini-graph-card**, **apexcharts-card**, **card-mod** (optional).
2. Settings > Dashboards > Ev (or create a new dashboard first to compare side by side).
3. ⋮ > Edit dashboard > ⋮ > Raw configuration editor, paste [`dashboard/dashboard.yaml`](dashboard/dashboard.yaml), Save.
4. Replace every `# EDIT` entity. Developer tools > States has the real IDs. A broken ID shows a red "Entity not available" tile, which makes leftovers easy to spot.

Requires Home Assistant 2024.8+ (sections view, tile features, `perform-action`).

## Views

| View | Icon | What is on it |
|------|------|---------------|
| Ev | home | badges, greeting, weather, GLaDOS + app shortcuts, lights with brightness/colour-temp sliders, Hue scenes, Apple devices |
| Sistem | server | Proxmox CPU/RAM gauges, graphs, VM/LXC status, disks |
| Ağ | lan | Keenetic status, throughput, speedtest |
| Medya | filmstrip | now playing, qBittorrent, Radarr/Sonarr |
| Güvenlik | shield | CrowdSec decisions and alert trend |
| Gelir | chart | RevenueCat MRR, subscribers, trend |
| Trendler | line chart | temperature and battery history |

## Design choices (from researching popular dashboards)

- Core tile/heading/sections cards first, custom cards only for charts: fewer things to break on HA updates.
- Tile `features` (brightness, colour temp, trend graph) replace the big separate slider bars the old Işıklar column used.
- Scenes as small vertical tiles on a 3-column grid, one heading per room.
- Status-first: badges up top, `visibility` rules hide the update badge when nothing is pending.
- One clear primary action per tile, strict grid, red/orange/green only where it carries meaning.
