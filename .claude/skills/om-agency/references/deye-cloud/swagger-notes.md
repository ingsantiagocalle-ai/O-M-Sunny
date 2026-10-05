# Notas por endpoint (Swagger /v2/api-docs)

> Generado por `scripts/update_deye_api.py` desde https://us1-developer.deyecloud.com/v2/api-docs (sync 2026-10-05 16:17 UTC; JSON reparado por typo de Deye). **No editar a mano.** Aquí viven los límites y la semántica que el catálogo MCP no trae (significado de `granularity`, ventanas máximas, etc.).

### `POST /v1.0/account/info`

Query relationship between account and the organization it belongs to

Query which company the account belongs to and the role of the account

### `POST /v1.0/account/token`

Obtain token

The token serves as the credential for accessing resources. Currently, registration via mobile number, email address, or username is supported on DeyeCloud. Users can choose one of three options for login (either the mobile, email, or username field is required;When the field mobile is used, the field countryCode must also be included). The password must be sha256 encrypted. If companyId is not provided, the token retrieved will correspond to the Personal user. When companyId is provided, the token retrieved will correspond to the business member
companyId can be obtained through endpoints ‘/v1.0/account/info’

### `POST /v1.0/config/battery`

Obtain battery-ralated parameter value

Retrieve the values of the parameters: battLowCapacity, battShutDownCapacity, maxChargeCurrent, and maxDischargeCurrent

### `POST /v1.0/config/system`

Obtain system work mode ralated parameter value

### `POST /v1.0/config/tou`

Obtain time of use configuration

### `POST /v1.0/device/addLogger`

Add loggers to business account. Up to 10 devices per batch

this endpoint is only for business account.

### `POST /v1.0/device/alertList`

Retrieve device alert list using 10-digit Unix timestamp(in seconds)

If deviceId is not empty, query by deviceId; otherwise, query by deviceSn
startTimestamp and endTimestamp should not exceed 30 days

### `POST /v1.0/device/deleteLogger`

Remove loggers from business account. Up to 10 devices per batch

this endpoint is only for business account.

### `POST /v1.0/device/history`

Retrieve device history data

Returns history data for devices at different granularities.
granularity=1: the field ‘startAt’ should be in format 'yyyy-MM-dd’. Field 'measurePoints' has to be passed. Returns measure-point data for the day specified by ‘startAt’
granularity=2: the field ‘startAt’ and 'endAt’ should be in format 'yyyy-MM-dd’. Returns statistics data between ‘startAt’ and ‘endAt’ (up to 31 days) with intervals of one day
granularity=3: the field ‘startAt’ and 'endAt’ should be in format 'yyyy-MM’. Returns statistics  data between ‘startAt’ and ‘endAt’ (up to 12 months) with intervals of one month
granularity=4: the field ‘startAt’ and 'endAt’ should be in format 'yyyy’. Returns yearly statistics data between ‘startAt’ and ‘endAt’
Value for field of ‘measurePoints‘ could be got through endpint ‘/v1.0/device/measurePoints’

### `POST /v1.0/device/historyRaw`

Retrieve device history data by timestamp

startTimestamp and endTimestamp are in second-level and startTimestamp and endTimestamp should be within 5 days
Value for field of ‘measurePoints‘ could be got through endpoint ‘/v1.0/device/measurePoints’

### `POST /v1.0/device/latest`

Fetch latest data of devices, supporting querying in batch, up to 10 devices per batch

### `POST /v1.0/device/list`

Fetch device list for business members

### `POST /v1.0/device/measurePoints`

Fetch measure points according to deviceSn

### `POST /v1.0/device/register`

Add datalogger into station

If get errors:device no upload records found.
Please:1. Check whether gatewaySn and deviceSn are right;
2.If gatewaySn and deviceSn are both right, please do wifi-configuration firstly

### `POST /v1.0/order/battery/modeControl`

Enable or disable the chargeMode

chargeMode: GRID_CHARGE; GEN_CHARGE; can be enabled or disabled

### `POST /v1.0/order/battery/parameter/update`

Set the value of battery-related parameter

Set the value for MAX_CHARGE_CURRENT, MAX_DISCHARGE_CURRENT, GRID_CHARGE_AMPERE, BATT_LOW
e.g.Field `paramterType`=MAX_CHARGE_CURRENT, Field value=the value you want to set

### `POST /v1.0/order/battery/type/update`

Set battery type

If the inverter type is Three phase LV Hybrid or Single phase LV Hybrid, 4 battery types supported: BATT_V;BATT_SOC;LI;NO_BATTERY
If the inverter type is Three phase HV Hybrid, 3 battery types supported: BATT_V;LI;NO_BATTERY

### `POST /v1.0/order/customControl`

send command in modbus protcol

Content should be generated according to modbus protocol
Contact service@deye.com.cn to get the inverter modbus protocol manual

### `POST /v1.0/order/gridPeakShaving/control`

Enable/disable grid peak shaving

Grid Peak-shaving: 
When it is active, grid output power will be limited within the set value.
If the load power exceeds the allowed value, it will take PV energy and battery as supplement. If still can’t meet the load requirement, grid power will increase to meet the load needs.

### `POST /v1.0/order/smartload/update`

Set parameter of smartload

Set smartload settings as 'smartload output', fill in the field 'deviceSn', set other parameters as null
Set offVoltage/onVoltage or onSOC/offSOC in pairs.
Please refer to user manual for the offVoltage/onVoltage range. The voltage range varies for different models of devices,if setting exceeds the voltage range may not take effect.
The approximate reference range is:
Three phase HV Hybrid:150-800;
Three phase LV Hybrid:38-60;
Single phase LV Hybrid:20-60

### `POST /v1.0/order/sys/energyPattern/update`

Set energy pattern as BATTERY_FIRST or LOAD_FIRST

### `POST /v1.0/order/sys/limitControl`

Set limit control function as SELL_FIRST,ZERO_EXPORT_TO_UPS_LOAD,ZERO_EXPORT_TO_CT or ZERO_EXPORT_TO_WIRELESS_CT

Only Micro Ess is supported.

### `POST /v1.0/order/sys/power/update`

Set the value for MAX_SELL_POWER or MAX_SOLAR_POWER

Hybrid 3Phase and 1Phase inverter support max_sell_power(`powerType`= MAX_SELL_POWER), max_solar_power Control(`powerType`= MAX_SOLAR_POWER) and zero_export_power(`powerType`= ZERO_EXPORT_POWER)
Microinverter and String inverter only support max solar power, the value of max solar power should not exceed rated power
MicroESS supports MaxToGridPower((`powerType`= MAX_SELL_POWER)) , the value of `MaxToGridPower` should not exceed rated power

### `POST /v1.0/order/sys/solarSell/control`

Enable or disable solarsell

Enable: action=on; Disable: action=off

### `POST /v1.0/order/sys/tou/switch`

Switch of TOU

Turn off TOU: 'action'=off, not necessary to fill in the field 'days'
Turn on TOU: 'action'=on, If you don't fill in the field 'days', by default, MONDAY to SUNDAY are all active
Fill in 'days' specifying which day you want to make active. For example days=[MONDAY, THURSDAY] means MONDAY and THURSDAY are active;TUESDAY,WEDNESDAY,FRIDAY,SATURDAY,SUNDAY are inactive
Notice:
value in field 'days' should be in uppercase

### `POST /v1.0/order/sys/tou/update`

Set time of use for the device

Supported Device Type: 3Phase & 1Phase Hybrid inverter; Micro Storage System(no voltage setting)
TimeFormat: 02:00 and timesettings  have to be in 5-minute intervals.For example(02:05,02:10)
If SOC, power, or voltage you set exceeds the range specified on LC screen or manual, it will be set to its boundary value

### `POST /v1.0/order/sys/workMode/update`

set system work mode as SELLING_FIRST,ZERO_EXPORT_TO_LOAD or ZERO_EXPORT_TO_CT

### `GET /v1.0/order/{orderId}`

Get the result of command execution

Status=666, command excutes successfully
orderResult: original command result in modbus
analysisResult: command result is parsed into the register address format(Due to differences in the way commands are issued, it may be consistent with orderResult.

### `POST /v1.0/station/alertList`

Retrieve Alert List for stations

Retrieve the alert list using 10-digit Unix timestamps (in seconds) for stations, with support for paginated queries.
 The difference between startTimestamp and endTimestamp must not exceed 180 days.

### `POST /v1.0/station/create`

Create a station

The field `currency` comply with ISO 4217 three-letter code standard. Please refer to https://www.iban.com/currency-codes
The field `timezone` comply with IANA time zone database standard.Please refer to https://en.wikipedia.org/wiki/List_of_tz_database_time_zones
The field `countryCode` comply with ISO_3166 alpha-2code standard. Please refer to https://en.wikipedia.org/wiki/ISO_3166-1_alpha-2

### `POST /v1.0/station/detail`

Fetch detail of a single station

Fetch the detail of the station by a given stationId, instead of paging through the station list.

### `POST /v1.0/station/device`

Fetch device list of the station in batch

Fetch the list of devices under the power station in batch(up to 10 stations per batch).If you want to query one station, pass one stationId in arraySupport for pagination queries

### `POST /v1.0/station/history`

Retrieve history data of the station

Retrieve history data of the station, supporting interval data queries in frames, days, months, and years.
The meaning of granularity is as follow:
If granularity is 1(frame), the field 'startAt' should be in format 'yyyy-MM-dd'. Return the data at 'startAt' with intervals of frame(Only support power-related data in repsonse)
If granularity is 2(day), the field 'startAt' and 'endAt'should be in format 'yyyy-MM-dd'. Return the data from 'startAt' to 'endAt'(excluded) (up to 31 days) with intervals of one day, 
If granularity is 3(month), the field 'startAt' and 'endAt'should be in format 'yyyy-MM'. Return the data for a certain number of months (up to 12 months)with intervals of one month
If granularity is 4(year), the field 'startAt' and 'endAt'should be in format 'yyyy'. Return the yearly data between 'startAt' to 'endAt'

### `POST /v1.0/station/history/power`

Retrieve history data of the station by timestamps in seconds(10-digit)

startTimestamp-endTimestamp should <=12months

### `POST /v1.0/station/latest`

Fetch latest data of the station

Retrieve latest data of the station

### `POST /v1.0/station/list`

Fetch station list under the account

### `POST /v1.0/station/listWithDevice`

Fetch station list under the account along with its devices

Fetch station list with devices
DeviceType query supports: INVERTER; MICRO_INVERTER; COLLECTOR; BATTERY; MECD; METER; RELAY_BOX; OPTIMIZER; PV_MODULE

### `POST /v1.0/strategy/dynamicControl`

Dynamic Control

The parameter you don't set will be kept the value it was.

### `POST /v1.0/strategy/dynamicControl/read`

Read Control

send read command to read the parameters of dynamic Control. After send the command, get the current parameters via endpoint /v1.0/strategy/dynamicControl/readResult

### `POST /v1.0/strategy/dynamicControl/readResult`

Query the result of current Dynamic Control

Please send endpoint /v1.0/strategy/dynamicControl/read first to get the orderId, then use this endpoint to query the result.
