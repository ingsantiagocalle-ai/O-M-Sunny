# Catálogo de endpoints DeyeCloud OpenAPI

> Generado por `scripts/update_deye_api.py` desde https://developer.deyecloud.com/api (servidor MCP v1.2.0, sync 2026-10-05 16:17 UTC). **No editar a mano.**

Todos los endpoints requieren el header `Authorization: Bearer <token>` salvo `/v1.0/account/token` (que usa `appId` por query). Base URL por región: ver SKILL.md.

## Account Operation

### `POST /v1.0/account/info`

Query relationship between account and the organization it belongs to

### `POST /v1.0/account/token`

Obtain token

| Param | En | Req. | Tipo | Descripción |
|---|---|---|---|---|
| `appId` | query | sí | string | appId,Example:201911067156002 |
| `host` | header |  | string | host |

Body (`tokenRequest`):

| Campo | Tipo | Req. | Notas |
|---|---|---|---|
| `appSecret` | string | sí | ej: 1q3e2ee5w5w20ww |
| `companyId` | integer |  | ej: 12 |
| `countryCode` | string |  | ej: 86 |
| `email` | string |  | ej: 13255@gmail.com |
| `mobile` | string |  | ej: 13255200000 |
| `password` | string | sí | must be sha256 encrypted; ej: 5994471abb01112afcc18159f6cc74b4f511b99806da59b3caf5a9c173cacfc5 |
| `username` | string |  | ej: deye |

## Configuration Operation

### `POST /v1.0/config/battery`

Obtain battery-ralated parameter value

Body (`DeviceConfigPointRequest`):

| Campo | Tipo | Req. | Notas |
|---|---|---|---|
| `deviceSn` | string | sí | ej: 12583SS |

### `POST /v1.0/config/system`

Obtain system work mode ralated parameter value

Body (`DeviceConfigPointRequest`):

| Campo | Tipo | Req. | Notas |
|---|---|---|---|
| `deviceSn` | string | sí | ej: 12583SS |

### `POST /v1.0/config/tou`

Obtain time of use configuration

Body (`DeviceConfigPointRequest`):

| Campo | Tipo | Req. | Notas |
|---|---|---|---|
| `deviceSn` | string | sí | ej: 12583SS |

## Control Operation

### `POST /v1.0/order/battery/modeControl`

Enable or disable the chargeMode

Body (`BaseDeviceOrderBatteryModeActionRequest`):

| Campo | Tipo | Req. | Notas |
|---|---|---|---|
| `action` | string | sí | action=on:enable, action=off:disable; ej: on |
| `batteryModeType` | string | sí | valores: GEN_CHARGE, GRID_CHARGE |
| `deviceSn` | string | sí |  |

### `POST /v1.0/order/battery/parameter/update`

Set the value of battery-related parameter

Body (`BaseDeviceOrderBatterySetPointRequest`):

| Campo | Tipo | Req. | Notas |
|---|---|---|---|
| `deviceSn` | string | sí |  |
| `paramterType` | string | sí | valores: MAX_CHARGE_CURRENT, MAX_DISCHARGE_CURRENT, GRID_CHARGE_AMPERE, BATT_LOW |
| `value` | integer | sí |  |

### `POST /v1.0/order/battery/type/update`

Set battery type

Body (`BaseDeviceOrderBatteryTypeSetRequest`):

| Campo | Tipo | Req. | Notas |
|---|---|---|---|
| `batteryType` | string | sí | ej: BATT_V |
| `deviceSn` | string | sí |  |

### `POST /v1.0/order/customControl`

send command in modbus protcol

Body (`DeviceCustomControlRequest`):

| Campo | Tipo | Req. | Notas |
|---|---|---|---|
| `content` | string | sí | modus protocol command; ej: 0103000102ABCD |
| `deviceSn` | string | sí |  |
| `timeoutSeconds` | integer |  | range,10~600; ej: 600 |

### `POST /v1.0/order/gridPeakShaving/control`

Enable/disable grid peak shaving

Body (`BaseDeviceGridPeakShavingControlRequest`):

| Campo | Tipo | Req. | Notas |
|---|---|---|---|
| `action` | string | sí | ej: on |
| `deviceSn` | string | sí |  |
| `power` | integer | sí | If this value is not set, it keep it was |

### `POST /v1.0/order/smartload/update`

Set parameter of smartload

Body (`BaseDeviceSmartLoadRequest`):

| Campo | Tipo | Req. | Notas |
|---|---|---|---|
| `deviceSn` | string | sí |  |
| `deviceType` | string |  | default is INVERTER Options: INVERTER;MICRO_INVERTER;MICRO_STORAGE_IN_ONE;MECD; valores: INVERTER, COMBINER_BOX, BATTERY, WEATHER_STATION, METER, AIR_CONDITIONING, OTHER_TYPE, HARMONIC_METER, QUALITY_MONITOR, SMART_HOME, SOLAR_TRACKING_CONTROLLER, SOLAR_RADIATION_SPECTROMETER, DTU, REPEATER, MICRO_INVERTER, PV_MODULE, ELECTRIC_SOURCE, COLLECTOR, FAN, WATER_PUMP, HYBRID_POWER_SYSTEM_CABINET, STEAM_ENGINE, EPM, GAS_METER, WATER_METER, SMART_METER, TYPE_RF_SUB_DEVICE, TYPE_OFF_GRID_INVERTER, MECD, BOX_TRANSFORMER, SWITCHGEAR, OPTIMIZER, DC_CONVERTER, SURGE_PROTECTION, FLOW_METER_THERMOMETER, RELAY_BOX, FEED_IN_LIMIT, MICRO_STORAGE_IN_ONE, OPTIMIZER_CONCENTRATOR; ej: INVERTER |
| `offSOC` | integer |  | smartload off battery SOC |
| `offVoltage` | integer |  | smartload off battery voltage |
| `onGridAlwaysOn` | boolean |  | true-enable 'on grid alwasys on'; false-disable 'on grid alwasys on' |
| `onSOC` | integer |  | smartload on battery SOC |
| `onVoltage` | integer |  | smartload on battery voltage |

### `POST /v1.0/order/sys/energyPattern/update`

Set energy pattern as BATTERY_FIRST or LOAD_FIRST

Body (`BaseDeviceOrderSysEnergyPatternRequest`):

| Campo | Tipo | Req. | Notas |
|---|---|---|---|
| `deviceSn` | string | sí |  |
| `energyPattern` | string | sí | options:BATTERY_FIRST;LOAD_FIRST; valores: BATTERY_FIRST, LOAD_FIRST; ej: BATTERY_FIRST |

### `POST /v1.0/order/sys/limitControl`

Set limit control function as SELL_FIRST,ZERO_EXPORT_TO_UPS_LOAD,ZERO_EXPORT_TO_CT or ZERO_EXPORT_TO_WIRELESS_CT

Body (`DeviceLimitControlFunctionRequest`):

| Campo | Tipo | Req. | Notas |
|---|---|---|---|
| `deviceSn` | string | sí |  |
| `limitControlFunctionType` | string | sí | options:SELL_FIRST;ZERO_EXPORT_TO_UPS_LOAD;ZERO_EXPORT_TO_CT;ZERO_EXPORT_TO_WIRELESS_CT; valores: SELL_FIRST, ZERO_EXPORT_TO_UPS_LOAD, ZERO_EXPORT_TO_CT, ZERO_EXPORT_TO_WIRELESS_CT; ej: SELL_FIRST |

### `POST /v1.0/order/sys/power/update`

Set the value for MAX_SELL_POWER or MAX_SOLAR_POWER

Body (`BaseDeviceOrderSysSetPointRequest`):

| Campo | Tipo | Req. | Notas |
|---|---|---|---|
| `deviceSn` | string | sí |  |
| `powerType` | string | sí | valores: MAX_SELL_POWER, MAX_SOLAR_POWER, ZERO_EXPORT_POWER |
| `value` | integer | sí |  |

### `POST /v1.0/order/sys/solarSell/control`

Enable or disable solarsell

Body (`BaseDeviceOrderSolarSellControlRequest`):

| Campo | Tipo | Req. | Notas |
|---|---|---|---|
| `action` | string | sí | action=on:enable solar sell, action=off:disable soalr sell; ej: on |
| `deviceSn` | string | sí |  |

### `POST /v1.0/order/sys/tou/switch`

Switch of TOU

Body (`BaseDeviceOrderTOUSwitchRequest`):

| Campo | Tipo | Req. | Notas |
|---|---|---|---|
| `action` | string | sí | ej: on |
| `days` | array[string] |  | If action is on, fill this field with the days of the week you want to switch on |
| `deviceSn` | string | sí |  |

### `POST /v1.0/order/sys/tou/update`

Set time of use for the device

Body (`BaseDeviceOrderTOUSetRequest`):

| Campo | Tipo | Req. | Notas |
|---|---|---|---|
| `deviceSn` | string | sí |  |
| `timeUseSettingItems` | array[TimeUseSettingItem] | sí | set the strategy for 6 time intervals.Have to be passed in sequence |

### `POST /v1.0/order/sys/workMode/update`

set system work mode as SELLING_FIRST,ZERO_EXPORT_TO_LOAD or ZERO_EXPORT_TO_CT

Body (`BaseDeviceOrderSysWorkModeRequest`):

| Campo | Tipo | Req. | Notas |
|---|---|---|---|
| `deviceSn` | string | sí |  |
| `workMode` | string | sí | options:SELLING_FIRST;ZERO_EXPORT_TO_LOAD;ZERO_EXPORT_TO_CT;For micro storage:GREEN_POWER_MODE;FULL_CHARGE_MODE;CUSTOMIZED_MODE; valores: SELLING_FIRST, ZERO_EXPORT_TO_LOAD, ZERO_EXPORT_TO_CT, GREEN_POWER_MODE, FULL_CHARGE_MODE, CUSTOMIZED_MODE; ej: SELLING_FIRST |

### `GET /v1.0/order/{orderId}`

Get the result of command execution

| Param | En | Req. | Tipo | Descripción |
|---|---|---|---|---|
| `language` | query |  | string | language |
| `orderId` | path | sí | integer | orderId |

## Device Operation

### `POST /v1.0/device/addLogger`

Add loggers to business account. Up to 10 devices per batch

Body (`LoggerRequest`):

| Campo | Tipo | Req. | Notas |
|---|---|---|---|
| `deviceSns` | array[string] |  |  |

### `POST /v1.0/device/alertList`

Retrieve device alert list using 10-digit Unix timestamp(in seconds)

| Param | En | Req. | Tipo | Descripción |
|---|---|---|---|---|
| `language` | query |  | string | language |

Body (`DeviceAlertListRequest`):

| Campo | Tipo | Req. | Notas |
|---|---|---|---|
| `deviceSn` | string |  |  |
| `endTimestamp` | integer | sí | ej: 1574132094 |
| `page` | integer |  | which page to display. default is 1 if not provided; ej: 1 |
| `size` | integer |  | size of one page，default is 20, max is 100; ej: 20 |
| `startTimestamp` | integer | sí | ej: 1574132075 |

### `POST /v1.0/device/deleteLogger`

Remove loggers from business account. Up to 10 devices per batch

Body (`LoggerRequest`):

| Campo | Tipo | Req. | Notas |
|---|---|---|---|
| `deviceSns` | array[string] |  |  |

### `POST /v1.0/device/history`

Retrieve device history data

Body (`DeviceHistoryDataRequest`):

| Campo | Tipo | Req. | Notas |
|---|---|---|---|
| `deviceSn` | string | sí | ej: 12583SS |
| `endAt` | string |  | Coule be null if granularity=1, Others is same with startAt; ej: 2024-01-01 |
| `granularity` | integer | sí | ej: 4 |
| `measurePoints` | array[string] |  |  |
| `startAt` | string | sí | ej: 2019-11-18 |

### `POST /v1.0/device/historyRaw`

Retrieve device history data by timestamp

Body (`DeviceHistoryPowerRequest`):

| Campo | Tipo | Req. | Notas |
|---|---|---|---|
| `deviceSn` | string | sí | ej: 12583SS |
| `endTimestamp` | integer | sí | ej: 173316200 |
| `measurePoints` | array[string] | sí |  |
| `startTimestamp` | integer | sí | ej: 1733155200 |

### `POST /v1.0/device/latest`

Fetch latest data of devices, supporting querying in batch, up to 10 devices per batch

Body (`latestDataRequest`):

| Campo | Tipo | Req. | Notas |
|---|---|---|---|
| `deviceList` | array[string] | sí | ej: ['12583SS'] |

### `POST /v1.0/device/list`

Fetch device list for business members

Body (`DeviceListRequest`):

| Campo | Tipo | Req. | Notas |
|---|---|---|---|
| `page` | integer |  | page number,default=1; ej: 1 |
| `size` | integer |  | page size，max:200, default=20; ej: 20 |

### `POST /v1.0/device/measurePoints`

Fetch measure points according to deviceSn

Body (`DeviceMeasurePointsRequest`):

| Campo | Tipo | Req. | Notas |
|---|---|---|---|
| `deviceSn` | string | sí | ej: 12583SS |
| `deviceType` | string |  | default is INVERTER Options: INVERTER;MICRO_INVERTER;MICRO_STORAGE_IN_ONE;MECD; valores: INVERTER, COMBINER_BOX, BATTERY, WEATHER_STATION, METER, AIR_CONDITIONING, OTHER_TYPE, HARMONIC_METER, QUALITY_MONITOR, SMART_HOME, SOLAR_TRACKING_CONTROLLER, SOLAR_RADIATION_SPECTROMETER, DTU, REPEATER, MICRO_INVERTER, PV_MODULE, ELECTRIC_SOURCE, COLLECTOR, FAN, WATER_PUMP, HYBRID_POWER_SYSTEM_CABINET, STEAM_ENGINE, EPM, GAS_METER, WATER_METER, SMART_METER, TYPE_RF_SUB_DEVICE, TYPE_OFF_GRID_INVERTER, MECD, BOX_TRANSFORMER, SWITCHGEAR, OPTIMIZER, DC_CONVERTER, SURGE_PROTECTION, FLOW_METER_THERMOMETER, RELAY_BOX, FEED_IN_LIMIT, MICRO_STORAGE_IN_ONE, OPTIMIZER_CONCENTRATOR; ej: INVERTER |

### `POST /v1.0/device/register`

Add datalogger into station

| Param | En | Req. | Tipo | Descripción |
|---|---|---|---|---|
| `language` | query |  | string | language |

Body (`DeviceRegisterRequest`):

| Campo | Tipo | Req. | Notas |
|---|---|---|---|
| `deviceSn` | string | sí | deviceSn cannot be empty |
| `gatewaySn` | string | sí |  |
| `stationId` | integer | sí |  |

## Station Operation

### `POST /v1.0/station/alertList`

Retrieve Alert List for stations

Body (`BaseStationAlertListRequest`):

| Campo | Tipo | Req. | Notas |
|---|---|---|---|
| `endTimestamp` | integer | sí | ej: 1733796958 |
| `page` | integer |  | page number,default=1; ej: 1 |
| `size` | integer |  | size for one page，max=200, default=20; ej: 20 |
| `startTimestamp` | integer | sí | ej: 1728526558 |
| `stationId` | integer | sí | ej: 322 |

### `POST /v1.0/station/create`

Create a station

Body (`BaseStationCreateRequest`):

| Campo | Tipo | Req. | Notas |
|---|---|---|---|
| `constructionCost` | number |  | ej: 2300.0 |
| `contactPhone` | string |  | ej: 13101969190 |
| `currency` | string | sí | ej: USD |
| `gridInterconnectionType` | string | sí | valores: DISTRIBUTED_FULLY, EXCESS, OFF_GRID, BATTERY_BACKUP, GROUND_FULLY, CENTRALIZED_FULLY, GEN_USE_BTR, GEN_USE, GRID_USE_BTR, USE_BTR; ej: DISTRIBUTED_FULLY |
| `installationAzimuthAngle` | number |  |  |
| `installationTiltAngle` | number |  |  |
| `installedCapacity` | number | sí |  |
| `locationAddress` | string | sí |  |
| `locationLat` | number | sí | station latitude |
| `locationLng` | number | sí | station Longitude |
| `mergeElectricPrice` | number |  | unitPrice（currency/kWh） |
| `name` | string | sí |  |
| `ownerCompany` | string |  |  |
| `ownerName` | string |  |  |
| `region` | Region | sí |  |
| `startOperatingTime` | string |  |  |
| `stationImage` | string |  |  |
| `type` | string |  | valores: HOUSE_ROOF, COMMERCIAL_ROOF, INDUSTRIAL_ROOF, GROUND |

### `POST /v1.0/station/device`

Fetch device list of the station in batch

Body (`deviceListRequest`):

| Campo | Tipo | Req. | Notas |
|---|---|---|---|
| `page` | integer |  | page,default:1; ej: 1 |
| `size` | integer |  | size for one page,max:200,default:20; ej: 20 |
| `stationIds` | array[integer] | sí | stationIds; ej: [322] |

### `POST /v1.0/station/history`

Retrieve history data of the station

Body (`BaseStationHistoryDataRequest`):

| Campo | Tipo | Req. | Notas |
|---|---|---|---|
| `endAt` | string |  | End date; ej: 2024 |
| `granularity` | integer | sí | The granularity of the telemetry data.; ej: 4 |
| `startAt` | string | sí | Start date; ej: 2024 |
| `stationId` | integer | sí | station ID; ej: 322 |

### `POST /v1.0/station/history/power`

Retrieve history data of the station by timestamps in seconds(10-digit)

Body (`BaseStationHistoryPowerRequest`):

| Campo | Tipo | Req. | Notas |
|---|---|---|---|
| `endTimestamp` | integer | sí |  |
| `startTimestamp` | integer | sí |  |
| `stationId` | integer | sí | station ID; ej: 322 |

### `POST /v1.0/station/latest`

Fetch latest data of the station

Body (`BaseStationRealTimeDataRequest`):

| Campo | Tipo | Req. | Notas |
|---|---|---|---|
| `stationId` | integer | sí | stationId; ej: 322 |

### `POST /v1.0/station/list`

Fetch station list under the account

Body (`BaseStationListRequest`):

| Campo | Tipo | Req. | Notas |
|---|---|---|---|
| `page` | integer |  | page,default value is 1; ej: 3 |
| `size` | integer |  | size for one page，default value is 20, max value is:200; ej: 50 |

### `POST /v1.0/station/listWithDevice`

Fetch station list under the account along with its devices

Body (`BaseStationWithDeviceListRequest`):

| Campo | Tipo | Req. | Notas |
|---|---|---|---|
| `deviceType` | string |  | valores: INVERTER, COMBINER_BOX, BATTERY, WEATHER_STATION, METER, AIR_CONDITIONING, OTHER_TYPE, HARMONIC_METER, QUALITY_MONITOR, SMART_HOME, SOLAR_TRACKING_CONTROLLER, SOLAR_RADIATION_SPECTROMETER, DTU, REPEATER, MICRO_INVERTER, PV_MODULE, ELECTRIC_SOURCE, COLLECTOR, FAN, WATER_PUMP, HYBRID_POWER_SYSTEM_CABINET, STEAM_ENGINE, EPM, GAS_METER, WATER_METER, SMART_METER, TYPE_RF_SUB_DEVICE, TYPE_OFF_GRID_INVERTER, MECD, BOX_TRANSFORMER, SWITCHGEAR, OPTIMIZER, DC_CONVERTER, SURGE_PROTECTION, FLOW_METER_THERMOMETER, RELAY_BOX, FEED_IN_LIMIT, MICRO_STORAGE_IN_ONE, OPTIMIZER_CONCENTRATOR; ej: INVERTER |
| `page` | integer |  | page,default value:1; ej: 3 |
| `size` | integer |  | size for one page,default value is 20, max value is:50; ej: 20 |

## Strategy Operation

### `POST /v1.0/strategy/dynamicControl`

Dynamic Control

Body (`BaseDynamicControlRequest`):

| Campo | Tipo | Req. | Notas |
|---|---|---|---|
| `deviceSn` | string | sí |  |
| `gridChargeAction` | string |  | gridChargeAction has to be one of on;off; ej: on |
| `gridChargeAmpere` | integer |  |  |
| `maxSellPower` | integer |  |  |
| `maxSolarPower` | integer |  |  |
| `solarSellAction` | string |  | solarSellAction has to be one of on;off; ej: on |
| `timeUseSettingItems` | array[TimeUseSettingItem] |  | set the strategy for 6 time intervals.Have to be passed in sequence |
| `touAction` | string |  | touAction has to be one of on;off; ej: on |
| `touDays` | array[string] |  | If action is on, fill this field with the days of the week you want to switch on |
| `workMode` | string |  | options:SELLING_FIRST;ZERO_EXPORT_TO_LOAD;ZERO_EXPORT_TO_CT; valores: SELLING_FIRST, ZERO_EXPORT_TO_LOAD, ZERO_EXPORT_TO_CT, GREEN_POWER_MODE, FULL_CHARGE_MODE, CUSTOMIZED_MODE; ej: SELLING_FIRST |
| `zeroExportPower` | integer |  |  |

### `POST /v1.0/strategy/dynamicControl/read`

Read Control

Body (`DynamicReadRequest`):

| Campo | Tipo | Req. | Notas |
|---|---|---|---|
| `deviceSn` | string | sí |  |

### `POST /v1.0/strategy/dynamicControl/readResult`

Query the result of current Dynamic Control

Body (`DynamicReadResultRequest`):

| Campo | Tipo | Req. | Notas |
|---|---|---|---|
| `orderId` | integer |  |  |
