# Herramientas del servidor Deye Open MCP

> Generado por `scripts/update_deye_api.py` (servidor v1.2.0, 51 tools, sync 2026-10-05 15:52 UTC). **No editar a mano.**

| Tool | Argumentos | Descripción |
|---|---|---|
| `list_data_centers` | — | List supported DeyeCloud developer API data centers. |
| `get_skill_info` | `client_skill_version` | Get deye-open-mcp skill information and check for updates. |
| `list_deye_endpoints` | `tag`, `keyword` | List bundled DeyeCloud OpenAPI endpoint summaries. |
| `get_server_info` | — | Return the current Deye Open MCP server version and update guidance. |
| `get_access_token` | `app_id`, `app_secret`, `email`, `password`, `data_center` | Obtain a DeyeCloud access token using app credentials and account credentials. |
| `call_deye_api` | `method`*, `path`*, `body`, `query`, `access_token`, `data_center`, `require_auth` | Call any DeyeCloud OpenAPI endpoint by HTTP method and path. |
| `list_stations` | `page`, `size`, `access_token`, `data_center` | Fetch station list under the account. |
| `list_station_devices` | `station_id`*, `page`, `size`, `access_token`, `data_center` | Fetch devices of one station. |
| `list_devices` | `page`, `size`, `access_token`, `data_center` | Fetch device list for business members. |
| `get_device_latest` | `device_list`*, `access_token`, `data_center` | Fetch latest data of devices, up to 10 devices per batch. |
| `get_station_latest` | `station_id`*, `access_token`, `data_center` | Fetch latest data of one station. |
| `get_order_result` | `order_id`*, `access_token`, `data_center` | Get the result of a control command by orderId. |
| `account_info` | `access_token`, `data_center` | Query relationship between account and the organization it belongs to. Standard wrapper for POST /v1.0/account/info. |
| `account_token` | `app_id`, `app_secret`, `email`, `password`, `data_center` | Obtain token. Standard wrapper for POST /v1.0/account/token. |
| `config_battery` | `body`, `access_token`, `data_center` | Obtain battery-ralated parameter value. Standard wrapper for POST /v1.0/config/battery. |
| `config_system` | `body`, `access_token`, `data_center` | Obtain system work mode ralated parameter value. Standard wrapper for POST /v1.0/config/system. |
| `config_tou` | `body`, `access_token`, `data_center` | Obtain time of use configuration. Standard wrapper for POST /v1.0/config/tou. |
| `device_add_logger` | `body`, `access_token`, `data_center` | Add loggers to business account. Up to 10 devices per batch. Standard wrapper for POST /v1.0/device/addLogger. |
| `device_alert_list` | `body`, `language`, `access_token`, `data_center` | Retrieve device alert list using 10-digit Unix timestamp(in seconds). Standard wrapper for POST /v1.0/device/alertList. |
| `device_delete_logger` | `body`, `access_token`, `data_center` | Remove loggers from business account. Up to 10 devices per batch. Standard wrapper for POST /v1.0/device/deleteLogger. |
| `device_history` | `body`, `page`, `size`, `access_token`, `data_center` | Retrieve device history data with pagination. |
| `device_history_raw` | `body`, `page`, `size`, `access_token`, `data_center` | Retrieve device history data by timestamp with pagination. |
| `device_latest` | `body`, `access_token`, `data_center` | Fetch latest data of devices, supporting querying in batch, up to 10 devices per batch. Standard wrapper for POST /v1.0/device/latest. |
| `device_list` | `body`, `access_token`, `data_center` | Fetch device list for business members. Standard wrapper for POST /v1.0/device/list. |
| `device_measure_points` | `body`, `access_token`, `data_center` | Fetch measure points according to deviceSn. Standard wrapper for POST /v1.0/device/measurePoints. |
| `device_register` | `body`, `language`, `access_token`, `data_center` | Add datalogger into station. Standard wrapper for POST /v1.0/device/register. |
| `order_battery_mode_control` | `body`, `access_token`, `data_center` | Enable or disable the chargeMode. Standard wrapper for POST /v1.0/order/battery/modeControl. |
| `order_battery_parameter_update` | `body`, `access_token`, `data_center` | Set the value of battery-related parameter. Standard wrapper for POST /v1.0/order/battery/parameter/update. |
| `order_battery_type_update` | `body`, `access_token`, `data_center` | Set battery type. Standard wrapper for POST /v1.0/order/battery/type/update. |
| `order_custom_control` | `body`, `access_token`, `data_center` | send command in modbus protcol. Standard wrapper for POST /v1.0/order/customControl. |
| `order_grid_peak_shaving_control` | `body`, `access_token`, `data_center` | Enable/disable grid peak shaving. Standard wrapper for POST /v1.0/order/gridPeakShaving/control. |
| `order_smartload_update` | `body`, `access_token`, `data_center` | Set parameter of smartload |
| `order_sys_energy_pattern_update` | `body`, `access_token`, `data_center` | Set energy pattern as BATTERY_FIRST or LOAD_FIRST. Standard wrapper for POST /v1.0/order/sys/energyPattern/update. |
| `order_sys_limit_control` | `body`, `access_token`, `data_center` | Set limit control function as SELL_FIRST,ZERO_EXPORT_TO_UPS_LOAD,ZERO_EXPORT_TO_CT or ZERO_EXPORT_TO_WIRELESS_CT. Standard wrapper for POST /v1.0/order/sys/limitControl. |
| `order_sys_power_update` | `body`, `access_token`, `data_center` | Set the value for MAX_SELL_POWER or MAX_SOLAR_POWER. Standard wrapper for POST /v1.0/order/sys/power/update. |
| `order_sys_solar_sell_control` | `body`, `access_token`, `data_center` | Enable or disable solarsell. Standard wrapper for POST /v1.0/order/sys/solarSell/control. |
| `order_sys_tou_switch` | `body`, `access_token`, `data_center` | Switch of TOU. Standard wrapper for POST /v1.0/order/sys/tou/switch. |
| `order_sys_tou_update` | `body`, `access_token`, `data_center` | Set time of use for the device. Standard wrapper for POST /v1.0/order/sys/tou/update. |
| `order_sys_work_mode_update` | `body`, `access_token`, `data_center` | set system work mode as SELLING_FIRST,ZERO_EXPORT_TO_LOAD or ZERO_EXPORT_TO_CT. Standard wrapper for POST /v1.0/order/sys/workMode/update. |
| `order_by_order_id` | `order_id`*, `language`, `access_token`, `data_center` | Get the result of command execution. Standard wrapper for GET /v1.0/order/{orderId}. |
| `station_alert_list` | `body`, `access_token`, `data_center` | Retrieve Alert List for stations. Standard wrapper for POST /v1.0/station/alertList. |
| `station_create` | `body`, `access_token`, `data_center` | Create a station. Standard wrapper for POST /v1.0/station/create. |
| `station_device` | `body`, `access_token`, `data_center` | Fetch device list of the station in batch. Standard wrapper for POST /v1.0/station/device. |
| `station_history` | `body`, `page`, `size`, `access_token`, `data_center` | Retrieve history data of the station with pagination. |
| `station_history_power` | `body`, `page`, `size`, `access_token`, `data_center` | Retrieve history data of the station by timestamps (10-digit seconds). |
| `station_latest` | `body`, `access_token`, `data_center` | Fetch latest data of the station. Standard wrapper for POST /v1.0/station/latest. |
| `station_list` | `body`, `access_token`, `data_center` | Fetch station list under the account. Standard wrapper for POST /v1.0/station/list. |
| `station_list_with_device` | `body`, `access_token`, `data_center` | Fetch station list under the account along with its devices. Standard wrapper for POST /v1.0/station/listWithDevice. |
| `strategy_dynamic_control` | `body`, `access_token`, `data_center` | Dynamic Control. Standard wrapper for POST /v1.0/strategy/dynamicControl. |
| `strategy_dynamic_control_read` | `body`, `access_token`, `data_center` | Read Control. Standard wrapper for POST /v1.0/strategy/dynamicControl/read. |
| `strategy_dynamic_control_read_result` | `body`, `access_token`, `data_center` | Query the result of current Dynamic Control. Standard wrapper for POST /v1.0/strategy/dynamicControl/readResult. |

`*` = obligatorio.
