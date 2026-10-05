---
name: deye-open-mcp
description: Use Deye Open MCP tools to query and operate DeyeCloud stations, devices, telemetry, alarms, configuration, and order/control results through a configured MCP server.
version: 1.2.0
author: Deye Open MCP
license: MIT
platforms: [macos, linux, windows]
metadata:
  hermes:
    tags: [mcp, deyecloud, openapi, solar, inverter, energy-storage]
---

# Deye Open MCP

## Purpose

Use this skill when the user asks to work with DeyeCloud through a configured Deye Open MCP server.

Typical requests:

- List Deye data centers.
- Get a DeyeCloud access token.
- List stations, station devices, and devices.
- Query latest device or station data.
- Query history, raw power data, measure points, alerts, and account information.
- Inspect available Deye Open MCP tools/endpoints.
- Call a less common DeyeCloud OpenAPI wrapper through the generic MCP tool.
- Check an order/control command result.

This skill assumes an MCP server named `deye_open` is configured in the host agent. Tool names may be exposed with a client prefix such as `mcp_deye_open_*`.

## Required Setup

Before using this skill, the agent environment must have a Deye Open MCP server configured.

**Prerequisite: Register a Deye OpenAPI App.** If the user does not yet have an AppId, AppSecret, or other API credentials, they must first register a Deye OpenAPI application. Direct the user to open their browser and visit:

https://developer.deyecloud.com/app

If the user indicates they need to register, instruct your host client to automatically open the browser to this URL so the user can complete registration and obtain their credentials.

Remote example:

```yaml
mcp_servers:
  deye_open:
    url: "https://<your-current-domain>/mcp"
```

Local test example:

```yaml
mcp_servers:
  deye_open:
    url: "http://127.0.0.1:12050/mcp"
```

Deye app/account credentials are not MCP server deployment configuration. When credentials are needed, pass them as explicit MCP tool arguments such as `app_id`, `app_secret`, `email`, and `password` on `get_access_token` / `account_token`, then pass the resulting `access_token` to read/query tools.

**Skill version auto-check.**  At the start of each conversation session, call `get_skill_info` with your current version (see `version:` field at the top of this file):

```text
get_skill_info(client_skill_version="1.2.0")
```

If the response contains `update_available: true`, proactively tell the user an update is available and point them to `skill_download_url`.  Also check `update_hint` for the exact version comparison message.

Do not write credentials into this skill, chat history, source files, `.env`, public documentation, or shared MCP server configuration. The server may have a default `DEYE_DATA_CENTER`, but per-call `data_center` should be supplied when the user's account region is known.

Supported data centers:

| Value | Base URL |
|---|---|
| `eu` | `https://eu1-developer.deyecloud.com` |
| `am` | `https://us1-developer.deyecloud.com` |
| `india` | `https://india-developer.deyecloud.com` |

Default data center is usually `eu` unless the server is configured otherwise.

## Authentication First (Required)

This MCP server does NOT ship default credentials. Every read/query/control tool needs an authenticated DeyeCloud session. If you call a business tool without credentials, the server returns:

```text
Missing required credentials: app_id, app_secret, email, password
```

To avoid this, ALWAYS authenticate before any other tool:

1. First call `get_access_token` with the user's own DeyeCloud OpenAPI credentials:

```text
get_access_token(
  app_id="<user appId>",
  app_secret="<user appSecret>",
  email="<user DeyeCloud email>",
  password="<user password>",
  data_center="eu"   # eu | am | india, match the user's account region
)
# -> returns access_token
```

2. Then pass the returned `access_token` to every subsequent tool:

```text
get_station_latest(station_id=123456, access_token="<token from step 1>", data_center="eu")
list_stations(page=1, size=10, access_token="<token from step 1>", data_center="eu")
```

Rules:

- Do NOT call business tools (`list_stations`, `get_station_latest`, `device_*`, `station_*`, `order_*`, etc.) before obtaining a token.
- If the user has not provided DeyeCloud credentials yet, ASK for `app_id`, `app_secret`, `email`, `password`, and account region (`data_center`) instead of calling tools and hitting the credentials error.
- Where to get credentials: `app_id` and `app_secret` come from a registered Deye OpenAPI application. If the user does not have them, point them to the Deye developer platform at `https://developer.deyecloud.com/app` to register an application and obtain AppId/AppSecret; API reference is at `https://developer.deyecloud.com/api#/`. The `email`/`password` are the user's own DeyeCloud account login.
- Reuse the same `access_token` across calls in the session; only re-authenticate when it expires or the user switches accounts.
- Never print, log, or store the credentials or the token in plain text.

## MCP Tool Map

The MCP server exposes 49 tools in total: 10 helper/shortcut tools and 39 standard DeyeCloud OpenAPI endpoint wrappers. The host client may prefix tool names, for example `mcp_deye_open_list_stations`.

### Helper and Shortcut Tools

| Tool | Arguments | Use |
|---|---|---|
| `list_data_centers` | none | Show supported Deye data centers. |
| `get_skill_info` | `client_skill_version` | Check skill version and see if an update is available. |
| `list_deye_endpoints` | `tag`, `keyword` | Search/list bundled DeyeCloud OpenAPI wrappers. |
| `get_access_token` | `app_id`, `app_secret`, `email`, `password`, `data_center` | Obtain a DeyeCloud access token. |
<details>
<summary>请求示例值</summary>

```json
{
  "appSecret": "1q3e2ee5w5w20ww",
  "companyId": 12,
  "countryCode": 86,
  "email": "13255@gmail.com",
  "mobile": 13255200000,
  "password": "5994471abb01112afcc18159f6cc74b4f511b99806da59b3caf5a9c173cacfc5",
  "username": "deye"
}
```

</details>
<details>
<summary>响应示例值</summary>

```json
{
  "accessToken": "Bearer eyJhbGciOiJSUzI1NiIsInR5cC",
  "code": 1000000,
  "expiresIn": 5183999,
  "msg": "success",
  "refreshToken": "Bearer eyJhbGciOiJSUzI1NiIsInR5cC",
  "scope": "all",
  "success": true,
  "tokenType": "bearer",
  "uid": 3
}
```

</details>
| `call_deye_api` | `method`, `path`, `body`, `query`, `access_token`, `data_center`, `require_auth` | Generic call for less common DeyeCloud OpenAPI paths. |
| `list_stations` | `page`, `size`, `access_token`, `data_center` | List stations. |
<details>
<summary>请求示例值</summary>

```json
{
  "page": 3,
  "size": 50
}
```

</details>
<details>
<summary>响应示例值</summary>

```json
{
  "code": 1000000,
  "msg": "success",
  "stationList": [
    {
      "id": 10,
      "name": "Deye Staion38",
      "locationLat": 50.093321,
      "locationLng": 30.614547,
      "locationAddress": "Novie Bezradichi",
      "regionNationId": 232,
      "regionTimezone": "Europe/Helsinki",
      "gridInterconnectionType": "DISTRIBUTED_FULLY",
      "installedCapacity": 50.0,
      "startOperatingTime": 1705593600,
      "createdDate": 1705304227.0,
      "batterySOC": 0.0,
      "connectionStatus": "NORMAL",
      "generationPower": 0.0,
      "lastUpdateTime": 1711108284,
      "contactPhone": "",
      "ownerName": null
    }
  ],
  "success": true,
  "total": 1
}
```

</details>
| `list_station_devices` | `station_id`, `page`, `size`, `access_token`, `data_center` | List devices under a station. |
<details>
<summary>请求示例值</summary>

```json
{
  "page": 1,
  "size": 20,
  "stationIds": [
    322
  ]
}
```

</details>
<details>
<summary>响应示例值</summary>

```json
{
  "code": 1000000,
  "deviceListItems": [
    {
      "deviceSn": "2212228299",
      "deviceType": "INVERTER",
      "stationId": 10
    },
    {
      "deviceSn": "2775784642",
      "deviceType": "COLLECTOR",
      "stationId": 10
    }
  ],
  "msg": "success",
  "success": true,
  "total": 2
}
```

</details>
| `list_devices` | `page`, `size`, `access_token`, `data_center` | List account devices. |
<details>
<summary>请求示例值</summary>

```json
{
  "page": 1,
  "size": 20
}
```

</details>
<details>
<summary>响应示例值</summary>

```json
{
  "code": 1000000,
  "deviceList": [
    {
      "deviceSn": "2401110313",
      "deviceId": 37,
      "deviceType": "INVERTER",
      "deviceState": 1,
      "updateTime": 1711093038,
      "productId": "0_5407_1"
    }
  ],
  "msg": "success",
  "success": true,
  "total": 322
}
```

</details>
| `get_device_latest` | `device_list`, `access_token`, `data_center` | Query latest data for one or more device SNs. |
<details>
<summary>请求示例值</summary>

```json
{
  "deviceList": [
    "12583SS"
  ]
}
```

</details>
<details>
<summary>响应示例值</summary>

```json
{
  "code": 1000000,
  "deviceDataList": [
    {
      "collectionTime": 1679980600,
      "dataList": [
        {
          "key": "MI Voltage L2",
          "unit": "V",
          "value": 223.4
        }
      ],
      "deviceSn": "12583SS",
      "deviceState": 1,
      "deviceType": "INVERTER"
    }
  ],
  "msg": "success",
  "success": true
}
```

</details>
| `get_station_latest` | `station_id`, `access_token`, `data_center` | Query latest station data. |
<details>
<summary>请求示例值</summary>

```json
{
  "stationId": 322
}
```

</details>
<details>
<summary>响应示例值</summary>

```json
{
  "code": 1000000,
  "msg": "success",
  "success": true
}
```

</details>
| `get_order_result` | `order_id`, `access_token`, `data_center` | Check a submitted control/order result. |
<details>
<summary>响应示例值</summary>

```json
{
  "code": 1000000,
  "msg": "success",
  "success": true
}
```

</details>

### Standard Endpoint Wrappers

Standard wrapper names are based on the OpenAPI path and do not include HTTP method prefixes. Do not invent old names such as `post_station_history` unless the connected server actually exposes them.

| Group | Tool | Arguments | Use |
|---|---|---|---|
| Account | `account_info` | `access_token`, `data_center` | Query account and organization relationship. |
<details>
<summary>响应示例值</summary>

```json
{
  "code": 1000000,
  "msg": "success",
  "orgInfoList": [
    {
      "roleName": "admin"
    }
  ],
  "success": true
}
```

</details>
| Account | `account_token` | `app_id`, `app_secret`, `email`, `password`, `data_center` | Obtain token. |
<details>
<summary>请求示例值</summary>

```json
{
  "appSecret": "1q3e2ee5w5w20ww",
  "companyId": 12,
  "countryCode": 86,
  "email": "13255@gmail.com",
  "mobile": 13255200000,
  "password": "5994471abb01112afcc18159f6cc74b4f511b99806da59b3caf5a9c173cacfc5",
  "username": "deye"
}
```

</details>
<details>
<summary>响应示例值</summary>

```json
{
  "accessToken": "Bearer eyJhbGciOiJSUzI1NiIsInR5cC",
  "code": 1000000,
  "expiresIn": 5183999,
  "msg": "success",
  "refreshToken": "Bearer eyJhbGciOiJSUzI1NiIsInR5cC",
  "scope": "all",
  "success": true,
  "tokenType": "bearer",
  "uid": 3
}
```

</details>
| Config | `config_battery` | `body`, `access_token`, `data_center` | Read battery-related parameter values. |
<details>
<summary>请求示例值</summary>

```json
{
  "deviceSn": "12583SS"
}
```

</details>
<details>
<summary>响应示例值</summary>

```json
{
  "code": 1000000,
  "msg": "success",
  "success": true
}
```

</details>
| Config | `config_system` | `body`, `access_token`, `data_center` | Read system work mode related parameter values. |
<details>
<summary>请求示例值</summary>

```json
{
  "deviceSn": "12583SS"
}
```

</details>
<details>
<summary>响应示例值</summary>

```json
{
  "code": 1000000,
  "msg": "success",
  "success": true
}
```

</details>
| Config | `config_tou` | `body`, `access_token`, `data_center` | Read time-of-use configuration. |
<details>
<summary>请求示例值</summary>

```json
{
  "deviceSn": "12583SS"
}
```

</details>
<details>
<summary>响应示例值</summary>

```json
{
  "code": 1000000,
  "msg": "success",
  "success": true,
  "timeUseSettingItems": [
    {
      "enableGeneration": false,
      "enableGridCharge": false
    }
  ]
}
```

</details>
| Device | `device_add_logger` | `body`, `access_token`, `data_center` | Add loggers to a business account. |
<details>
<summary>请求示例值</summary>

```json
{
  "deviceSns": [
    "<deviceSns>"
  ]
}
```

</details>
<details>
<summary>响应示例值</summary>

```json
{
  "code": 1000000,
  "msg": "success",
  "success": true
}
```

</details>
| Device | `device_alert_list` | `body`, `language`, `access_token`, `data_center` | Retrieve device alert list. |
<details>
<summary>请求示例值</summary>

```json
{
  "endTimestamp": 1574132094,
  "page": 1,
  "size": 20,
  "startTimestamp": 1574132075
}
```

</details>
<details>
<summary>响应示例值</summary>

```json
{
  "alertList": [
    {
      "alertCode": 2,
      "alertName": "AC_NoUtillity_Fault F35",
      "impact": 2,
      "level": 1,
      "protocolName": "ERR5"
    }
  ],
  "code": 1000000,
  "deviceId": 252525,
  "deviceSn": "12583SS",
  "deviceType": "C0LLECTOR",
  "msg": "success",
  "success": true,
  "total": 322
}
```

</details>
| Device | `device_delete_logger` | `body`, `access_token`, `data_center` | Remove loggers from a business account. |
<details>
<summary>请求示例值</summary>

```json
{
  "deviceSns": [
    "<deviceSns>"
  ]
}
```

</details>
<details>
<summary>响应示例值</summary>

```json
{
  "code": 1000000,
  "msg": "success",
  "success": true
}
```

</details>
| Device | `device_history` | `body`, `page`, `size`, `access_token`, `data_center` | Retrieve device history data with pagination. |
<details>
<summary>请求示例值</summary>

```json
{
  "deviceSn": "12583SS",
  "endAt": "2024-01-01",
  "granularity": 4,
  "measurePoints": [
    "<measurePoints>"
  ],
  "startAt": "2019-11-18"
}
```

</details>
<details>
<summary>响应示例值</summary>

```json
{
  "code": 1000000,
  "dataList": [
    {
      "collectionTime": "2023",
      "itemList": [
        {
          "key": "generation",
          "value": "9292.00",
          "unit": "kWh",
          "name": "Production"
        }
      ]
    }
  ],
  "deviceId": 252525,
  "deviceSn": "12583SS",
  "deviceType": "C0LLECTOR",
  "granularity": 4,
  "msg": "success",
  "success": true,
  "_page": 1,
  "_size": 20,
  "_total_items": 365,
  "_total_pages": 19
}
```

</details>
| Device | `device_history_raw` | `body`, `page`, `size`, `access_token`, `data_center` | Retrieve raw device history by timestamp with pagination. |
<details>
<summary>请求示例值</summary>

```json
{
  "deviceSn": "12583SS",
  "endTimestamp": 173316200,
  "measurePoints": [
    "<measurePoints>"
  ],
  "startTimestamp": 1733155200
}
```

</details>
<details>
<summary>响应示例值</summary>

```json
{
  "code": 1000000,
  "dataList": [
    {
      "itemList": []
    }
  ],
  "deviceId": 252525,
  "deviceSn": "12583SS",
  "deviceType": "C0LLECTOR",
  "msg": "success",
  "success": true,
  "_page": 1,
  "_size": 20,
  "_total_items": 1440,
  "_total_pages": 72
}
```

</details>
| Device | `device_latest` | `body`, `access_token`, `data_center` | Fetch latest device data in batches up to 10 devices. |
<details>
<summary>请求示例值</summary>

```json
{
  "deviceList": [
    "12583SS"
  ]
}
```

</details>
<details>
<summary>响应示例值</summary>

```json
{
  "code": 1000000,
  "deviceDataList": [
    {
      "collectionTime": 1679980600,
      "dataList": [
        {
          "key": "MI Voltage L2",
          "unit": "V",
          "value": 223.4
        }
      ],
      "deviceSn": "12583SS",
      "deviceState": 1,
      "deviceType": "INVERTER"
    }
  ],
  "msg": "success",
  "success": true
}
```

</details>
| Device | `device_list` | `body`, `access_token`, `data_center` | Fetch device list for business members. |
<details>
<summary>请求示例值</summary>

```json
{
  "page": 1,
  "size": 20
}
```

</details>
<details>
<summary>响应示例值</summary>

```json
{
  "code": 1000000,
  "deviceList": [
    {
      "deviceSn": "2401110313",
      "deviceId": 37,
      "deviceType": "INVERTER",
      "deviceState": 1,
      "updateTime": 1711093038,
      "productId": "0_5407_1"
    }
  ],
  "msg": "success",
  "success": true,
  "total": 322
}
```

</details>
| Device | `device_measure_points` | `body`, `access_token`, `data_center` | Fetch measure points by device SN. |
<details>
<summary>请求示例值</summary>

```json
{
  "deviceSn": "12583SS",
  "deviceType": "INVERTER"
}
```

</details>
<details>
<summary>响应示例值</summary>

```json
{
  "code": 1000000,
  "measurePoints": [
    "SOC",
    "TotalChargeEnergy"
  ],
  "msg": "success",
  "success": true
}
```

</details>
| Device | `device_register` | `body`, `language`, `access_token`, `data_center` | Add datalogger into station. |
<details>
<summary>响应示例值</summary>

```json
{
  "code": 1000000,
  "gatewayId": 200124803,
  "msg": "success",
  "success": true
}
```

</details>
| Order/Control | `order_battery_mode_control` | `body`, `access_token`, `data_center` | Enable or disable battery charge mode. |
<details>
<summary>请求示例值</summary>

```json
{
  "action": "on",
  "batteryModeType": "GEN_CHARGE"
}
```

</details>
<details>
<summary>响应示例值</summary>

```json
{
  "code": 1000000,
  "collectionTime": 1615900034,
  "msg": "success",
  "success": true
}
```

</details>
| Order/Control | `order_battery_parameter_update` | `body`, `access_token`, `data_center` | Set battery-related parameter value. |
<details>
<summary>请求示例值</summary>

```json
{
  "paramterType": "MAX_CHARGE_CURRENT"
}
```

</details>
<details>
<summary>响应示例值</summary>

```json
{
  "code": 1000000,
  "collectionTime": 1615900034,
  "msg": "success",
  "success": true
}
```

</details>
| Order/Control | `order_battery_type_update` | `body`, `access_token`, `data_center` | Set battery type. |
<details>
<summary>请求示例值</summary>

```json
{
  "batteryType": "BATT_V"
}
```

</details>
<details>
<summary>响应示例值</summary>

```json
{
  "code": 1000000,
  "collectionTime": 1615900034,
  "msg": "success",
  "success": true
}
```

</details>
| Order/Control | `order_custom_control` | `body`, `access_token`, `data_center` | Send custom Modbus protocol command. |
<details>
<summary>请求示例值</summary>

```json
{
  "content": "0103000102ABCD",
  "timeoutSeconds": 600
}
```

</details>
<details>
<summary>响应示例值</summary>

```json
{
  "code": 1000000,
  "collectionTime": 1615900034,
  "msg": "success",
  "success": true
}
```

</details>
| Order/Control | `order_grid_peak_shaving_control` | `body`, `access_token`, `data_center` | Enable or disable grid peak shaving. |
<details>
<summary>请求示例值</summary>

```json
{
  "action": "on"
}
```

</details>
<details>
<summary>响应示例值</summary>

```json
{
  "code": 1000000,
  "collectionTime": 1615900034,
  "msg": "success",
  "success": true
}
```

</details>
| Order/Control | `order_smartload_update` | `body`, `access_token`, `data_center` | Set smart load parameters. |
<details>
<summary>请求示例值</summary>

```json
{
  "deviceType": "INVERTER",
  "onGridAlwaysOn": false
}
```

</details>
<details>
<summary>响应示例值</summary>

```json
{
  "code": 1000000,
  "collectionTime": 1615900034,
  "msg": "success",
  "success": true
}
```

</details>
| Order/Control | `order_sys_energy_pattern_update` | `body`, `access_token`, `data_center` | Set energy pattern such as battery-first or load-first. |
<details>
<summary>请求示例值</summary>

```json
{
  "energyPattern": "BATTERY_FIRST"
}
```

</details>
<details>
<summary>响应示例值</summary>

```json
{
  "code": 1000000,
  "collectionTime": 1615900034,
  "msg": "success",
  "success": true
}
```

</details>
| Order/Control | `order_sys_limit_control` | `body`, `access_token`, `data_center` | Set export/limit control mode. |
<details>
<summary>请求示例值</summary>

```json
{
  "limitControlFunctionType": "SELL_FIRST"
}
```

</details>
<details>
<summary>响应示例值</summary>

```json
{
  "code": 1000000,
  "collectionTime": 1615900034,
  "msg": "success",
  "success": true
}
```

</details>
| Order/Control | `order_sys_power_update` | `body`, `access_token`, `data_center` | Set max sell power or max solar power. |
<details>
<summary>请求示例值</summary>

```json
{
  "powerType": "MAX_SELL_POWER"
}
```

</details>
<details>
<summary>响应示例值</summary>

```json
{
  "code": 1000000,
  "collectionTime": 1615900034,
  "msg": "success",
  "success": true
}
```

</details>
| Order/Control | `order_sys_solar_sell_control` | `body`, `access_token`, `data_center` | Enable or disable solar sell. |
<details>
<summary>请求示例值</summary>

```json
{
  "action": "on"
}
```

</details>
<details>
<summary>响应示例值</summary>

```json
{
  "code": 1000000,
  "collectionTime": 1615900034,
  "msg": "success",
  "success": true
}
```

</details>
| Order/Control | `order_sys_tou_switch` | `body`, `access_token`, `data_center` | Switch TOU on/off. |
<details>
<summary>请求示例值</summary>

```json
{
  "action": "on",
  "days": [
    "<days>"
  ]
}
```

</details>
<details>
<summary>响应示例值</summary>

```json
{
  "code": 1000000,
  "collectionTime": 1615900034,
  "msg": "success",
  "success": true
}
```

</details>
| Order/Control | `order_sys_tou_update` | `body`, `access_token`, `data_center` | Set device time-of-use configuration. |
<details>
<summary>请求示例值</summary>

```json
{
  "timeUseSettingItems": [
    {
      "enableGeneration": false,
      "enableGridCharge": false,
      "enableSell": false
    }
  ]
}
```

</details>
<details>
<summary>响应示例值</summary>

```json
{
  "code": 1000000,
  "collectionTime": 1615900034,
  "msg": "success",
  "success": true
}
```

</details>
| Order/Control | `order_sys_work_mode_update` | `body`, `access_token`, `data_center` | Set system work mode. |
<details>
<summary>请求示例值</summary>

```json
{
  "workMode": "SELLING_FIRST"
}
```

</details>
<details>
<summary>响应示例值</summary>

```json
{
  "code": 1000000,
  "collectionTime": 1615900034,
  "msg": "success",
  "success": true
}
```

</details>
| Order/Control | `order_by_order_id` | `order_id`, `language`, `access_token`, `data_center` | Get command execution result. |
<details>
<summary>响应示例值</summary>

```json
{
  "code": 1000000,
  "msg": "success",
  "success": true
}
```

</details>
| Station | `station_alert_list` | `body`, `access_token`, `data_center` | Retrieve station alert list. |
<details>
<summary>请求示例值</summary>

```json
{
  "endTimestamp": 1733796958,
  "page": 1,
  "size": 20,
  "startTimestamp": 1728526558,
  "stationId": 322
}
```

</details>
<details>
<summary>响应示例值</summary>

```json
{
  "code": 1000000,
  "msg": "success",
  "stationAlertItems": "stationAlertItems",
  "success": true,
  "total": 322
}
```

</details>
| Station | `station_create` | `body`, `access_token`, `data_center` | Create a station. |
<details>
<summary>请求示例值</summary>

```json
{
  "constructionCost": 2300.0,
  "contactPhone": 13101969190,
  "currency": "USD",
  "gridInterconnectionType": "DISTRIBUTED_FULLY",
  "region": {
    "countryCode": "AU",
    "timezone": "Europe/Istanbul"
  },
  "type": "HOUSE_ROOF"
}
```

</details>
<details>
<summary>响应示例值</summary>

```json
{
  "code": 1000000,
  "id": 1234,
  "msg": "success",
  "success": true
}
```

</details>
| Station | `station_device` | `body`, `access_token`, `data_center` | Fetch station device list in batch. |
<details>
<summary>请求示例值</summary>

```json
{
  "page": 1,
  "size": 20,
  "stationIds": [
    322
  ]
}
```

</details>
<details>
<summary>响应示例值</summary>

```json
{
  "code": 1000000,
  "deviceListItems": [
    {
      "deviceSn": "2212228299",
      "deviceType": "INVERTER",
      "stationId": 10
    },
    {
      "deviceSn": "2775784642",
      "deviceType": "COLLECTOR",
      "stationId": 10
    }
  ],
  "msg": "success",
  "success": true,
  "total": 2
}
```

</details>
| Station | `station_history` | `body`, `page`, `size`, `access_token`, `data_center` | Retrieve station history data with pagination. |
<details>
<summary>请求示例值</summary>

```json
{
  "endAt": 2024,
  "granularity": 4,
  "startAt": 2024,
  "stationId": 322
}
```

</details>
<details>
<summary>响应示例值</summary>

```json
{
  "code": 1000000,
  "msg": "success",
  "stationDataItems": [
    {
      "generationPower": null,
      "consumptionPower": null,
      "gridPower": null,
      "purchasePower": null,
      "wirePower": null,
      "chargePower": null,
      "dischargePower": null,
      "batteryPower": null,
      "batterySOC": null,
      "irradiateIntensity": null,
      "generationValue": 182.6,
      "generationRatio": 0.0,
      "gridRatio": 0.0,
      "chargeRatio": 100.0,
      "consumptionValue": 242.5,
      "consumptionRatio": null,
      "purchaseRatio": 88.54369,
      "consumptionDischargeRatio": 11.45631,
      "gridValue": 364.2,
      "purchaseValue": 519.9,
      "chargeValue": 428.9,
      "dischargeValue": 399.6,
      "fullPowerHours": 18.26,
      "irradiate": null,
      "theoreticalGeneration": null,
      "pr": null,
      "cpr": null,
      "dateTime": null,
      "year": 2024,
      "month": 0,
      "day": 0
    }
  ],
  "success": true,
  "total": 1,
  "_page": 1,
  "_size": 20,
  "_total_items": 365,
  "_total_pages": 19
}
```

</details>
| Station | `station_history_power` | `body`, `page`, `size`, `access_token`, `data_center` | Retrieve station history power data by timestamp with pagination. |
<details>
<summary>请求示例值</summary>

```json
{
  "stationId": 322
}
```

</details>
<details>
<summary>响应示例值</summary>

```json
{
  "code": 1000000,
  "msg": "success",
  "stationDataItems": [],
  "success": true,
  "total": 1,
  "_page": 1,
  "_size": 20,
  "_total_items": 1440,
  "_total_pages": 72
}
```

</details>
| Station | `station_latest` | `body`, `access_token`, `data_center` | Fetch latest station data. |
<details>
<summary>请求示例值</summary>

```json
{
  "stationId": 322
}
```

</details>
<details>
<summary>响应示例值</summary>

```json
{
  "code": 1000000,
  "msg": "success",
  "success": true
}
```

</details>
| Station | `station_list` | `body`, `access_token`, `data_center` | Fetch station list. |
<details>
<summary>请求示例值</summary>

```json
{
  "page": 3,
  "size": 50
}
```

</details>
<details>
<summary>响应示例值</summary>

```json
{
  "code": 1000000,
  "msg": "success",
  "stationList": [
    {
      "id": 10,
      "name": "Deye Staion38",
      "locationLat": 50.093321,
      "locationLng": 30.614547,
      "locationAddress": "Novie Bezradichi",
      "regionNationId": 232,
      "regionTimezone": "Europe/Helsinki",
      "gridInterconnectionType": "DISTRIBUTED_FULLY",
      "installedCapacity": 50.0,
      "startOperatingTime": 1705593600,
      "createdDate": 1705304227.0,
      "batterySOC": 0.0,
      "connectionStatus": "NORMAL",
      "generationPower": 0.0,
      "lastUpdateTime": 1711108284,
      "contactPhone": "",
      "ownerName": null
    }
  ],
  "success": true,
  "total": 1
}
```

</details>
| Station | `station_list_with_device` | `body`, `access_token`, `data_center` | Fetch station list with devices. |
<details>
<summary>请求示例值</summary>

```json
{
  "deviceType": "INVERTER",
  "page": 3,
  "size": 20
}
```

</details>
<details>
<summary>响应示例值</summary>

```json
{
  "code": 1000000,
  "msg": "success",
  "stationList": [
    {
      "deviceListItems": [
        {
          "connectStatus": "0：Offline，1：Online，2: Alert",
          "deviceSn": 123,
          "deviceType": "INVERTER"
        }
      ],
      "gridInterconnectionType": "DISTRIBUTED_FULLY",
      "type": "HOUSE_ROOF"
    }
  ],
  "stationTotal": 1,
  "success": true
}
```

</details>
| Strategy | `strategy_dynamic_control` | `body`, `access_token`, `data_center` | Dynamic control. |
<details>
<summary>请求示例值</summary>

```json
{
  "gridChargeAction": "on",
  "solarSellAction": "on",
  "timeUseSettingItems": [
    {
      "enableGeneration": false,
      "enableGridCharge": false,
      "enableSell": false
    }
  ],
  "touAction": "on",
  "touDays": [
    "<touDays>"
  ],
  "workMode": "SELLING_FIRST"
}
```

</details>
<details>
<summary>响应示例值</summary>

```json
{
  "code": 1000000,
  "collectionTime": 1615900034,
  "msg": "success",
  "success": true
}
```

</details>
| Strategy | `strategy_dynamic_control_read` | `body`, `access_token`, `data_center` | Read dynamic control configuration. |
<details>
<summary>响应示例值</summary>

```json
{
  "code": 1000000,
  "collectionTime": 1615900034,
  "msg": "success",
  "success": true
}
```

</details>
| Strategy | `strategy_dynamic_control_read_result` | `body`, `access_token`, `data_center` | Query current dynamic control result. |
<details>
<summary>响应示例值</summary>

```json
{
  "code": 1000000,
  "gridChargeAction": "on",
  "msg": "success",
  "solarSellAction": "on",
  "success": true,
  "timeUseSettingItems": [
    {
      "enableGeneration": false,
      "enableGridCharge": false,
      "enableSell": false
    }
  ],
  "touAction": "on",
  "touDays": [
    "<touDays>"
  ],
  "workMode": "SELLING_FIRST"
}
```

</details>

### Tool Selection Rules

- Authenticate first: call `get_access_token` and reuse its `access_token`; do not call any business tool without it (see "Authentication First").
- Prefer helper tools for common workflows because their arguments are simpler.
- Use standard endpoint wrappers when the user asks for a specific DeyeCloud capability.
- Use `call_deye_api` only when no helper or standard wrapper matches the request.
- Treat every `order_*`, `station_create`, `device_register`, `device_add_logger`, and `device_delete_logger` call as potentially state-changing; require explicit user confirmation before calling.

## Usage Patterns

### Discover tools

When the user asks what the integration can do, call:

```text
list_deye_endpoints(keyword="station")
```

or list tools through the host MCP client if available.

### List data centers

```text
list_data_centers()
```

### Check skill version

```text
get_skill_info(client_skill_version="1.2.0")
```

Check the response for `update_available`: if `true`, tell the user to update their skill package.

### List stations

```text
list_stations(page=1, size=10, data_center="eu")
```

If the user does not specify a data center, use the server default unless there is reason to ask.

### List station devices

```text
list_station_devices(station_id=123456, page=1, size=10, data_center="eu")
```

### Query device latest data

```text
get_device_latest(device_list=["2212228299"], data_center="eu")
```

### Query station latest data

```text
get_station_latest(station_id=123456, data_center="eu")
```

### Generic endpoint call

Use `call_deye_api` only when no clearer helper tool exists:

```text
call_deye_api(
  method="POST",
  path="/v1.0/station/latest",
  body={"stationId": 123456},
  data_center="eu"
)
```

## Response Style

When returning Deye data to the user:

1. Summarize the result first.
2. Show important fields such as station name, station ID, device SN, device type, status, latest values, timestamps, and alarm status.
3. Preserve raw IDs exactly.
4. If the API returns an error, report `code`, `msg`, and `requestId` when available.
5. Do not expose access tokens, app secrets, passwords, or full credential payloads.

## Safety Rules

1. Read-only monitoring is safe by default: station list, device list, latest data, history, alerts, measure points, and endpoint discovery.
2. Control/order tools can change inverter or device behavior. Before calling any control/order/update tool, ask the user to explicitly confirm the target station/device and intended action.
3. Never call control/order/update tools based only on vague instructions such as “optimize it” or “change settings”. Ask for exact target and settings.
4. Never print or save `DEYE_APP_SECRET`, `DEYE_PASSWORD`, `DEYE_ACCESS_TOKEN`, or account credentials.
5. If authentication fails, check data center, app credentials, account credentials, and token format. Deye token password requests require SHA256 password handling, normally implemented by the MCP server.
6. If a tool or field name is unclear, inspect `list_deye_endpoints` or the connected tool schema rather than guessing.

## Troubleshooting

If tools are unavailable:

- Confirm the MCP server is configured as `deye_open` or check the host client's actual MCP server name.
- Confirm the server URL is reachable and points to the MCP endpoint, usually `/mcp`.
- Restart or reload the host agent after MCP config changes.
- Ask the user for the non-secret MCP server URL and visible error message if connection fails.

If authentication fails:

- Verify `DEYE_DATA_CENTER` matches the user's DeyeCloud account region.
- Verify `DEYE_APP_ID` and `DEYE_APP_SECRET` belong to the same DeyeCloud OpenAPI application.
- Verify `DEYE_EMAIL` and `DEYE_PASSWORD` are correct for DeyeCloud.
- Do not ask the user to paste secrets into chat unless their environment has an explicit secure secret-input flow.

## Quick Start Prompt for Users

After installing this skill and configuring the MCP server, users can ask:

```text
Load the deye-open-mcp skill. List my Deye stations, then show latest data for the first online device.
```
