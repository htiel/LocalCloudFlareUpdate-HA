# Cloudflare DDNS — Home Assistant Integration

A Home Assistant custom integration that automatically keeps your Cloudflare DNS `A` records updated with your home network's current public IPv4 address (Dynamic DNS / DDNS).

Unlike the built-in Cloudflare integration, this one supports **multiple zones and multiple records** from a single integration entry, and lets you update your selection at any time via the **Configure** button — no need to delete and re-add the integration.

---

## Features

- Automatically detects your current public IPv4 address
- Updates any number of Cloudflare DNS `A` records across one or more zones
- Runs on a configurable interval (default: every 60 minutes)
- Exposes a `cloudflare_ddns.update_records` service for instant manual updates from automations
- Full **Configure** UI in HA — change your zones and records without reinstalling
- Supports API token re-authentication without losing your config

---

## Requirements

- Home Assistant 2024.1 or later
- A Cloudflare account with one or more zones
- A Cloudflare **API Token** with the following permissions:
  - `Zone > Zone > Read`
  - `Zone > DNS > Edit`
  - Applied to **All zones** (or at least the zones you want to manage)

To create a token: Cloudflare Dashboard → My Profile → API Tokens → Create Token → Use the "Edit zone DNS" template.

---

## Installation via HACS

1. Make sure [HACS](https://hacs.xyz) is installed in your Home Assistant instance.
2. In HA, go to **HACS → ⋮ (menu) → Custom repositories**.
3. Add `https://github.com/Htiel/LocalCloudFlareUpdate-HA` as category **Integration**.
4. Search for **Cloudflare DDNS** in HACS and click **Download**.
5. Restart Home Assistant.

---

## Setup

1. Go to **Settings → Devices & Services → + Add Integration**.
2. Search for **Cloudflare DDNS**.
3. Follow the three-step setup wizard:
   - **Step 1 — API Token**: Enter your Cloudflare API token.
   - **Step 2 — Zones**: Select one or more of your Cloudflare zones (domains) to manage.
   - **Step 3 — Records**: Select the specific DNS `A` records within those zones to keep updated.
4. The integration will immediately check and update any stale records, then poll every 60 minutes.

---

## Reconfiguring Zones / Records

You can change your selected zones and records at any time without reinstalling:

1. Go to **Settings → Devices & Services**.
2. Find the **Cloudflare DDNS** card and click **Configure**.
3. Update your zone and record selections and click **Submit**.

The integration will reload automatically with the new settings.

---

## Services

### `cloudflare_ddns.update_records`

Triggers an immediate update of all configured DNS records with your current public IP. Useful in automations (e.g. on HA startup or network reconnect).

**Example automation:**
```yaml
automation:
  trigger:
    platform: homeassistant
    event: start
  action:
    service: cloudflare_ddns.update_records
```

---

## Troubleshooting

| Problem | Solution |
|---|---|
| "Could not get external IPv4 address" | HA cannot reach the internet. Check your network. |
| "invalid_auth" during setup | Your API token is incorrect or missing the required permissions. |
| Records not updating | Confirm the record names match exactly what appears in your Cloudflare dashboard (e.g. `home.example.com`, not just `home`). |
| Integration not appearing after install | Restart Home Assistant after installing via HACS. |

