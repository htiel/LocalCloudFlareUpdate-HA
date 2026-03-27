# Cloudflare DDNS — Home Assistant Integration

A Home Assistant custom integration that automatically keeps your Cloudflare DNS `A` records updated with your home network's current public IPv4 address (Dynamic DNS / DDNS).

Unlike the built-in Cloudflare integration, this one supports **multiple zones and multiple records** from a single integration entry, and lets you update your selection at any time via the **Configure** button — no need to delete and re-add the integration.

---

## Credits & Attribution

This integration is based on the official **Home Assistant Cloudflare integration**:
- Source: [github.com/home-assistant/core](https://github.com/home-assistant/core/tree/dev/homeassistant/components/cloudflare)
- Documentation: [home-assistant.io/integrations/cloudflare](https://www.home-assistant.io/integrations/cloudflare)
- Original authors: [@ludeeus](https://github.com/ludeeus) and [@ctalkington](https://github.com/ctalkington)

The original work is licensed under the [Apache License 2.0](https://www.apache.org/licenses/LICENSE-2.0). This project is a derivative work under the same license.

Extended and enhanced by [@Htiel](https://github.com/Htiel) with assistance from **GitHub Copilot (Claude Sonnet)**, adding:
- Multi-zone and multi-record support
- In-UI reconfiguration via the Configure button (options flow)
- Last sync timestamp and status sensors
- Manual sync button entity
- Configurable poll interval with low-interval warnings
- Duplicate record safety checks

---

## Features

- Automatically detects your current public IPv4 address
- Updates any number of Cloudflare DNS `A` records across one or more zones
- Runs on a configurable poll interval (default: 60 minutes, minimum: 5 minutes)
- Exposes a `cloudflare_ddns.update_records` service for instant manual updates from automations
- Full **Configure** UI in HA — change zones, records, and poll interval without reinstalling
- Supports API token re-authentication without losing your config
- Automatically migrates config entries from the original single-zone schema
- Skips duplicate updates — if the target IP already exists on a record name, no redundant API call is made
- All entities grouped under a single **Cloudflare DDNS** device card in HA

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
4. The integration will immediately check and update any stale records, then poll on the configured interval (default 60 minutes).

---

## Entities

All entities appear under a single **Cloudflare DDNS** device card in **Settings → Devices & Services → Devices**.

### Sensors

| Entity | Description |
|---|---|
| **Last Sync** | Timestamp of the last successful sync attempt. Uses the `timestamp` device class so HA displays it as a formatted date/time. |
| **Sync Status** | Text summary of the most recent sync result. Possible values: `Pending` (never run), `Up to date` (nothing needed changing), `X record(s) updated` (records were updated), `Failed` (an error occurred). Also exposes a `records_updated` attribute containing the integer count of records changed in the last run. |

### Buttons

| Entity | Description |
|---|---|
| **Sync Now** | Press to trigger an immediate DNS update outside of the normal poll interval. Equivalent to calling the `cloudflare_ddns.update_records` service. |

---

## Reconfiguring

You can change your selected zones, records, or poll interval at any time without reinstalling:

1. Go to **Settings → Devices & Services**.
2. Find the **Cloudflare DDNS** card and click **Configure**.
3. **Step 1** — Update your zone selection and/or poll interval (in minutes).
   - Minimum interval: **5 minutes** (hard limit enforced in the UI).
   - A warning is shown if you set the interval below **15 minutes**; submit again to confirm.
4. **Step 2** — Update your DNS record selection.
5. Click **Submit**. The integration reloads automatically with the new settings.

### Adding a new record to track

If you want to start managing a new DNS record that doesn't exist yet:

1. In the **Cloudflare Dashboard**, go to your zone's **DNS** settings and add a new `A` record with any placeholder IP (e.g. `192.168.0.1`).
2. Back in Home Assistant, go to **Settings → Devices & Services**, find the **Cloudflare DDNS** card, and click **Configure**.
3. Work through the Configure steps and select the new record alongside your existing ones.
4. Click **Submit** — the integration will immediately update the new record to your current public IP.

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
| Sync Status stuck on "Pending" | The coordinator has not yet completed its first run. Wait for the first poll or press **Sync Now**. |
| Sync Status shows "Failed" | Check **Settings → System → Logs** and filter by `cloudflare_ddns` for the underlying error message. |
| "interval_too_low" error in Configure | The poll interval must be at least 5 minutes. |
| Re-authentication prompt appears | Your API token has been revoked or its permissions changed. Go to **Settings → Devices & Services**, find the Cloudflare DDNS card, and follow the re-auth prompt to enter a new token without losing your zone/record config. |

