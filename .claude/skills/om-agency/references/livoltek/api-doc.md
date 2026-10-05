# Documentación de la API de Livoltek v1.6.0 (copia de trabajo)

> Generado por `scripts/update_livoltek_api.py` desde `js/app.9f56d8e5.js` (sha256 `ef66ab8f67300d4b…`, 2026-10-05 21:09 UTC). **No editar a mano.** Última revisión del historial de la doc: 2025-01-20. Texto reconstruido del bundle Vue de https://api.livoltek-portal.com:8081/ess-api/ (International) y https://api-eu.livoltek-portal.com:8081/ess-api/ (Europa).
>
> Los tokens y contraseñas de **ejemplo** de la doc se sustituyeron por marcadores (`<token-de-ejemplo-omitido>`, `<md5-de-ejemplo-omitido>`). Las incoherencias de la propia doc (rutas, unidades, erratas) se listan aparte en `endpoints.md`, no se corrigen aquí.

## Índice

1. Purpose and scope
2. Acronyms and abbreviations
3. Revision History
4. Introduction
5. Technical Information
6. API Access
7. Security Best Practices
8. Language and Time Encoding
9. Request Format
10. Response Formats
11. Error Handling
12. Usage Limitations
13. Site List
14. Device List
15. Current power flow
16. Device generation or consumption
17. Site Details
18. Site Installer
19. Site generation overview
20. Site Historical Power Flow
21. Site Historical Active Power
22. Device Historical Alarm
23. Site Social Contribution
24. Storage Information
25. Device Details
26. Device technical parameters in recent 7 days
27. Site historical solar generation in recent 2 years
28. Site historical grid import&export in recent 2 years
29. API user login and get token
30. Charging station creation
31. Charging station query
32. Charging station update
33. Charging station deletion
34. Charging device creation
35. Charging device query
36. Charging device delete
37. Charging Record Query
38. Charging Station Start/Stop
39. Charging schedule settings
40. Mqtt push device alarm
41. Mqtt push device working status
42. Query the power station ID based on device SN
43. Site Owner
44. Device Basic Data
45. Device One Day Fault Alarm
46. Generate UserToken
47. UserToken query
48. Device power report query
49. Site day energy query
50. Sunspec reboot inverter
51. Sunspec reboot BMS
52. Sunspec some param info
53. Sunspec some param setting

## 1. Purpose and scope

The purpose of this document is to outline the Application Programming Interface (API) available via LIVOLTEK-PORTAL (a Cloud-Based Monitoring Platform).

The web services allow authorized users access to certain data (including personal information) output by or regarding such Systems (collectively, "Data").

This document provides information about the technical features of the API, and describes each API with its parameters formats and other details.

## 2. Acronyms and abbreviations

The following table lists acronyms used in this document

| Abbreviation | Meaning |
| --- | --- |
| API | Application Programing Interface |
| WS | Web Services |
| REST | Representational State Transfer |
| CSV | Comma Separated Values |
| JSON | JavaScript Object Notation |
| XML | Extensible Mark-up Language |

## 3. Revision History

January 20th 2025 -- Device basic information query and real time device information query, add query conditions

November 28th 2024-- Increase the return of the installer's organization code Add query for power plant owners

September 20th, 2024 -- Document revision

March 14th, 2024 -- Added a way to obtain MQTT usernames and passwords Add API for MQTT subscription messages

August 15th, 2023 -- Add a description of API call frequency restrictions<br> Modify some API descriptions

August 16, 2022 -- Add document introduction<br> Add a new API description

May 10, 2022 -- First draft

## 4. Introduction

For whom own, operate, manage, or interact with sites that include products that are manufactured by or for LIVOLTEK and third-party products, as applicable (jointly the "Products"), or are approved in writing by LIVOLTEK (each such installation, a "System"). The LIVOLTEK API allows you use a tool or services ( "Your Applications" ) to access to certain data (including personal information) output by or regarding such Systems (collectively, "Data"). <br>

Please read and asign LIVOLTEK SOFTWARE API LICENSE AGREEMENTS.<br> Link to<br>

> International servers: https://api.livoltek-portal.com:8081/ess-api/<br> Europe servers: https://api-eu.livoltek-portal.com:8081/ess-api/<br>

The following is a list of available APIs:

| API Name | API Output |
| --- | --- |
| Site List | Returns a list of sites related to the given token, which is the account api_key. This API accepts parameters for convenient search, sort and pagination.<br>Limit: Only support to 2 searh text at once; Only support to 1 sort text at once |
| Device List | Return the number of equipment in the specified site, equipment ID, equipment type (inverter, charging pile, electricity meter, etc.), equipment model, equipment SN and equipment manufacturer |
| Current power flow | Query the current energy flow of the specified power station to obtain the last update time, status of each system type, parameter unit (W) and value:<br>○ Photovoltaic working state (generating, offline) and power value,<br>○ Working state of power grid (importing, exporting) and power value,<br>○ Load working state ( consuming, idel) and power value,<br>○ Energy storage working state (charging, discharging, idel), power and SOC.<br>○ Working state of charger (available, EV charging) and power value<br>Reques by site ID.<br>* When there is no internal and external electricity meter connected in the system, there is no return value of the power grid |
| Device generation or consumption | Return device lifetime generation or consumption |
| Site Details | return details of the selected site, including site id, site name, site image, installation region, installation time zone and so on |
| Site Installer | return the installer company of the selected site |
| Site generation overview | Return generation review of selected site, including site name，amount of online equipment, latest updated timestamp, power, daily generation, monthly generation, yearly generation, lifetime generation, |
| Site Historical Power Flow | Query the energy flow of the specified site to obtain the update timestamp, status of each system type, parameter unit (W) and value in selected time duration:<br>○ Photovoltaic working state (generating, offline) and power value,<br>○ Working state of power grid (importing, exporting) and power value,<br>○ Load working state ( consuming, idel) and power value,<br>○ Energy storage working state (charging, discharging, idel), power and SOC.<br>○ Working state of charger (available, EV charging) and power value<br>Reques by site ID. and time duration<br>* When there is no internal and external electricity meter connected in the system, there is no return value of the power grid.<br>* start time should be within recent 7 days. |
| Site Historical Active Power | Query the historical power of the specified site to obtain the update timestamp, power value and unit (W) in selected time duration<br>* start time should be within recent 7 days. |
| Device Historical Alarm | Search device alarm logs in recent 7 days by device SN. |
| Site Social Contribution | Return site social contribution of last update time, CO2 reduce, Equivalent tree planting and standard coal reduced. |
| Storage Information | Query the information of the energy storage battery in the specified site to obtain the BAT capacity, BMS SN, current SOC/voltage, battery type, and power / voltage / SOC in recent 7 days, and daily charge and discharge capacity in recent 7 days |
| Device Details | Query the equipment information of the specified device to obtain the device model, SN, working condition (offline, normal, fault, etc.) and its update time, firmware version, device type and manufacturer. |
| Device technical parameters in recent 7 days | Query the real-time technical parameter data of the specified equipment to obtain the real-time data of the corresponding equipment, data update time and value, including the current / voltage of each MPPT, the voltage / current of three-phase power grid, power grid frequency, active power of power grid, apparent power of power grid, etc. <br>* in recent 7 days.<br>* Data interval is 5 minutes. |
| Site historical solar generation in recent 2 years | Query for site historical solar generation in specific time interval, including every day’s generation in the specified time period, with the unit of daily / weekly / monthly<br>* Limit: <br>1)When the unit is day / week, the start and end time should be within the past two years, <br>2)the interval (from start to end time)should not exceed 31 days with the unit “ day”, <br>3)the interval should not exceed 180 days with the unit “week”; |
| Site historical grid import&export in recent 2 years | Query the historical grid energy of the specified site, query the historical total solar generation(Wh), grid import energy(Wh), grid export energy(Wh) in the specified time period, with the unit of daily / weekly / monthly<br>* Limit: <br>1)When the unit is day / week, the start and end time should be within the past two years, <br>2)the interval (from start to end time)should not exceed 31 days with the unit “ day”, <br>3)the interval should not exceed 180 days with the unit “week”; |
| Charging station creation | Create a charging station. This station belongs to the user who calls the interface currently. The type of power station can only be a charging station |
| Charging station query | According to the query criteria, query the power station information under the user's name |
| Charging station update | Update power station information based on power station ID |
| Charging station deletion | Delete a user's charging station based on the charging station ID |
| Charging device access | Add charging equipment under the charging station |
| Charging device query | Query charging devices |
| Delete charging device | Delete charging device based on device ID |
| Charging record query | Query customer's charging records |
| Charging device start and stop | The charging device requires the SN of the charging station, the slogan of the charging gun, and the charging strategy to start and stop charging |
| Charging schedule settings | Charging schedule appointment, only one charging schedule can be made per day. If there are repeated appointments, the original charging schedule will be overwritten |
| API user login and get token | Get api user token and verify whether the API caller has permission |

API keys must be used in order to submit API requests. <br>

“Application” owner should use its SecurityID & Key, and "Products" or “Site” owner should generate an Account Level (for his/her account only) key.<br>

Display requirements:<br> When displaying information from the API, place the LIVOLTEK logo where it is clear to the user that the information source is LIVOLTEK’s monitoring system.<br>

The logo should link to <br>

> International servers: https://api.livoltek-portal.com:8081/ess-api/<br> Europe servers: https://api-eu.livoltek-portal.com:8081/ess-api/<br>

For any assistance with display, send an email to service@livoltek.com.<br>

## 5. Technical Information

The LIVOLTEK API is built as RESTful service:<br> • It responds with standard HTTP(s) codes.<br> • It can return results in JSON .

## 6. API Access

- The API can be accessed via HTTPS protocol only. LIVOLTEK monitoring server supports both HTTPS/1.0 and HTTPS/1.1 protocols.
- All APIs are secured via an access token: every access to the API requires a valid token as a HEADER parameter named Authorization.

For example:

```
Authorization:<token-de-ejemplo-omitido>
```

Some APIs require token tokens generated by the LIVOLTEK system to verify user information，This token serves as the parameter userToken for the URL.

For example:

```
userToken=<token-de-ejemplo-omitido>
```

- An token can be generated to enable access to specific sites (via Site token) or to all sites within a specific account (via Account token).

#### To get SecurityID & KEY for your application:

1. No Livoltek account:<br> Send an email to service@livoltek.com in following format:<br> Subject: Livoltek API Request.<br> Application name: name of your tool, service or app<br> Application description: brief description of your application<br> Requesting server: select the corresponding server based on the region, EMEA or International Powered by: copyright of your application<br>
2. Have Livoltek account:<br> Click on "Account Name" ->click on "My Profile" ->click on "Security ID" ->click on "Add".<br> Generate Security ID & KEY.<br> Special Reminder: Click the 'Copy' button on the right to copy the complete Security ID & KEY.<br>

![1]((imagen empaquetada en el bundle; no incluida))![2]((imagen empaquetada en el bundle; no incluida))

#### To generate an account users token:

Login https://www.livoltek-portal.com for International server users.<br> Login https://evs.livoltek-portal.com for EMEA server users.<br> In the **Account Admin** > **My Profile** > **Generate Token** tab > **Add** button:

1. Acknowledge reading and agreeing to the LIVOLTEK Software API License Agreements.<br>
2. Enter account password. <br>
3. Modify "Valid Through" date, when it is expired you may not be able to access . Please refer to " Generate UserToken" after getting the original token.
4. Click **Confirm**.<br>
5. Click **Copy**.<br>
6. Use the key in all API requests<br>

#### To get MQTT username and password

MQTT message subscription requires authentication of username and password.<br> Send an email to service@livoltek.com in following format:<br>Subject: Livoltek API MQTT message subscription.<br> Application name: name of your tool, service or app<br> Application description: A brief description of the application and the type of message subscribed to<br> Requesting server: select the corresponding server based on the region, EMEA or International<br> Powered by: copyright of your application<br>

## 7. Security Best Practices

To help keep your data secure from unauthorized access, make sure to adhere to the following best practices:<br> ○ **Don’t share your Token**. Remember, gaining access to a Token is equivalent to obtaining a user’s login credentials.<br>

- Never store your Token in publicly accessible locations, including shared documents, code repositories (such as GitHub) and shared network drives.<br>
- Avoid sharing your Token with third parties whenever possible. If you’re using a third party service that asks you for your LIVOLTEK Monitoring Token, it is your responsibility to ensure the provider stores and handles your Token in a secure manner.<br>
- Do not make API requests directly from browser applications (JavaScript code). If you store your Token in your publicly accessible JavaScript code, it can be easily copied by anyone visiting your site. API requests should only be made from a secure backend server.<br>

○ **Rotate your Token periodically**. LIVOLTEK recommends updating your Token every 6 months. To generate a new Token:<br>

- **Account Key** – Navigate to the **Account Admin** > **My Profile** > **Generate Token** tab > **Add** button<br>

1. Acknowledge reading and agreeing to the LIVOLTEK Software API License Agreements.<br>
2. Enter account password.<br>
3. Modify effective date. <br>
4. Click **Confirm**.<br>
5. Click **Copy**<br>
6. Use the key in all API requests<br>

## 8. Language and Time Encoding

When using special characters or spaces in URL, they must be **url encoded**.<br> The monitoring server data can be in different languages therefore data is retrieved using UTF-8.<br> Date and time formats in all APIs are timestamp.<br> All physical measures are in the metric units system.<br> Temperature values are always in Celsius degrees.<br>

## 9. Request Format

The request format and parameters are specified per each API, and conform to the HTTP and REST standards. Parameter order in the request is not significant.

## 10. Response Formats

The user can request data in the following formats:<br>

- JSON (application/json)<br>

See specific APIs in the next sections for supported format in each API.

## 11. Error Handling

The API system uses standard HTTP error codes for reporting errors that occurred while calling the API. The monitoring server API supports standard HTTP error codes, for example: if the user access is of an unknown resource, an HTTP 404 error will be returned.

## 12. Usage Limitations

> Usage limitations are enforced to prevent abuse of the API, and these limitations may be changed in the future without notice. Additionally, a request rate limit is applied to prevent abuse of the service. If you exceed the limitations, an error message appears in the monitoring server API. If the limitation is further exceeded, the system may temporarily be nonoperational, or your access to the monitoring server API may be blocked.<br>

#### User Account Token Usage Limitation

Each specific account token can be used up to 3 Source IP or Application SecurityID.<br> Any additional requests will result in HTTP 428 error - token occupied.

#### Hourly Limitation

API requests is subject to a query limit of 300 calls per hour for specific Source IP or Application SecurityID<br> For interfaces accessed by the same Source IP or Application SecurityID:<br>

- All interface can only make 300 calls per hour in summary.<br>
- Each interface can only make 300 calls per hour individually.<br>
- All account token can only make 300 calls per hour.<br>
- Each account token can only make 100 calls per hour.<br>

Any additional Application level request will result in HTTP 429 error - too many requests.

#### Minutely Limitation

For special users, all interfaces request 300 times a minute using the same security ID<br> Any additional Application level request will result in HTTP 429 error - too many requests.

#### Concurrency Limitation

The monitoring server API allows up to 3 concurrent API calls from **the same source IP**. <br> Any additional concurrent calls will return HTTP 429 error – too many requests.<br> To execute APIs concurrently without exceeding the above limitation, it is the client responsibility to implement a throttling mechanism on the client side.

## 13. Site List

> Returns a list of sites related to the given token, which is the account api_key. This API accepts parameters for convenient search, sort and pagination.Limit: Only support to 2 searh text at once; Only support to 1 sort text at once

> **URL**: /hess/api/userSites/list**Method**: GET**Header**: Header: Authorization : token

### Header Description

| Parameter | Type | Description |
| --- | --- | --- |
| Authorization | String | token |

### Request parameters

| Parameter | Type | Length | Description | Mandatory | note |
| --- | --- | --- | --- | --- | --- |
| userToken | String |  | User token | yes |  |
| userType | String | 2 | User Type | no | 0 - end-user（default)<br>1 - agent |
| powerStationType | String | 256 | Site type<br>1-Grid-tied solar system<br>2-Solar storage system<br>3-EV charging hub<br>4-EV charging hub with solar storage | no | Parameter:<br>1-Grid-tied solar system<br>2-Solar storage system<br>3-EV charging hub<br>4-EV charging hub with solar storage |
| createTime | Long | 13 | The time when this site is being added to the system | no | Search text for this site |
| active | Integer | 1 | If the site is active<br>0-not active<br>1-active | no |  |
| country | String | 255 | The region where this site located | no | Search text for this site |
| sortField | String | 50 | A sorting option for this site list:<br>- pvCapacity<br>- updateTime | no |  |
| sortType | String | 5 | Sort order for the sort property. Allowed values ar ASC (ascending) and DESC (descending). | no |  |
| page | Int |  | The first site index to be returned in the results, default=1 | yes |  |
| size | Int |  | Pagesize of each page:<br>-5<br>-10 (default)<br>-30 | yes |  |

### Response Parameters

| Parameter | Type | Length | Description | Mandatory | note |
| --- | --- | --- | --- | --- | --- |
| powerStationId | String | 10 | Site ID |  |  |
| powerStationName | String | 64 | Site name |  |  |
| country | String | 255 | County/Region |  |  |
| administrativeRegion | String | 255 | administrative division |  | Under developing |
| powerStationType | String | 256 | Site type |  |  |
| powerStationStatus | Integer | 2 | Site communication status<br>1-all devices are online<br>2-all devices are offline<br>3-some devices in this site are offline |  |  |
| pvCapacity | Double | 12 | PV capacity |  | kWp |
| registrationTime | Timestamp |  | The time when this site is being added to the system |  | Example:<br>2022-06-08T09:06:16.000+0000 |
| updateTime | Long | 13 | The time for latest update of device in this site |  |  |
| active | Integer | 1 | If the site is active<br>2-not active<br>3-active |  |  |
| count | Integer |  | The amount of sites |  |  |
| timeZone | String |  | time zone |  |  |
| message | String |  | Message code<br>-SUCCESS<br>-FAIL |  |  |
| code | String |  | http/https response code<br>-200 ok<br>-201 Created<br>-401 Unauthorized<br>-403 Forbidden<br>-404 Not Found |  |  |

### Example

```
  https://api.livoltek-portal.com:8081/hess/api/userSites/list?userToken=1&createTime=1659705100000&active=1&sortType=asc&page=10&size=10&userType=1& powerStationType=1& country=CN& sortField= pvCapacity
```

### Response example

```
{
    "code": "String",
    "message": "String",
    "data": {
        "list": [{
                "powerStationId": " String ",
                "powerStationName": " String ",
                "country": " String ",
                "administrativeRegion":" String ",
                "timeZone": " String ",
                "powerStationType": " String ",
                "powerStationStatus":" Integer" ,
                "pvCapacity": " Double ",
                "registrationTime": " Timestamp ",
                "updateTime":," Long ",
                "active": " Integer",
                "agent": " Long"
            }],
        "count": " Integer"
    }
}

{
    "code": "200",
    "message": "SUCCESS",
    "data": {
        "list": [
            {
                "powerStationId": "11009",
                "powerStationName": "Maria Ilzanir",
                "country": "BR",
                "administrativeRegion": null,
                "timeZone": "America/Fortaleza",
                "powerStationType": "Grid-tied solar system",
                "powerStationStatus": 2,
                "pvCapacity": 2.7,
                "registrationTime": "2022-02-25T12:16:21.000+0000",
                "updateTime": 1655751244677,
                "active": 1,
                "agent": 129752657551361
            }
        ],
        "count": 14
    }
}
```

## 14. Device List

> Return the number of equipment in the specified site, equipment ID, equipment type (inverter, charging pile, electricity meter, etc.), equipment model, equipment SN and equipment manufacturer

> **URL**: /hess/api/device/{siteId}/list**Method**: GET**Header**: Header: Authorization : token

### Header Description

| Parameter | Type | Description |
| --- | --- | --- |
| Authorization | String | token |

### Request parameters

| Parameter | Type | Length | Description | Mandatory | constraint |
| --- | --- | --- | --- | --- | --- |
| userToken | String |  | User token | yes |  |
| userType | String | 2 | User Type | no | 0- end-user<br>1- agent |
| siteId | String | 10 | Site ID | yes |  |
| page | Int |  | The first site index to be returned in the results, default=1 | yes |  |
| size | Int |  | Pagesize of each page:<br>-5<br>-10 (default)<br>-30 | yes |  |

### Response Parameters

| Parameter | Type | Length | Description | Mandatory | constraint |
| --- | --- | --- | --- | --- | --- |
| count | Integer |  | The number of equipment in this site |  |  |
| id | Integer | 10 | Device id |  |  |
| inverterSn | String | 64 | Device SN(include inverter、 evcharger、collector …) |  |  |
| collectorSn | String | 64 | Device datalogger SN |  | Under developing |
| productType | String | 3 | Product type |  |  |
| deviceManufacturer | String |  | Device Manufacturer |  |  |
| deviceModel | String |  | Device type |  | Default Return: inverter |
| code | String |  | http/https response code<br>-200 ok<br>-201 Created<br>-401 Unauthorized<br>-403 Forbidden<br>-404 Not Found |  |  |
| message | String |  | Message code<br>-SUCCESS<br>-FAIL |  |  |

### Example

```
   https://api.livoltek-portal.com:8081/hess/api/device/527/list?userToken=1&page=1&size=10&userType=1
```

### Response example

```
{
    "code": " String ",
    "message": " String ",
    "data": {
        "list": [
            {
                "id": “Integer”,
                "inverterSn": " String ",
                "collectorSn": " String ",
                "productType": " String ",
                "deviceModel": " String ",
                "deviceManufacturer": " String "
            }
        ],
        "count": " Integer"
    }
}

{
    "code": "200",
    "message": "SUCCESS",
    "data": {
        "list": [
  {
                "id": 8,
                "inverterSn": "2045-96510381D",
                "collectorSn": "2045-96510381D",
                "productType": "GT3-50K",
                "deviceModel": "inverter",
                "deviceManufacturer": "LIVOLTEK"
            }
        ],
        "count": 2
    }
}
```

## 15. Current power flow

> Query the current energy flow of the specified power station to obtain the last update time, status of each system type, parameter unit (W) and value:

- Photovoltaic working state (generating, offline) and power value,
- Working state of power grid (importing, exporting) and power value,
- Load working state ( consuming, idel) and power value,
- Energy storage working state (charging, discharging, idel), power and SOC.
- Working state of charger (available, EV charging) and power value

> Reques by site ID.<br>*When there is no internal and external electricity meter connected in the system, there is no return value of the power grid.

> **URL**: /hess/api/site/{siteId}/curPowerflow**Method**: GET**Header**: Header: Authorization : token

### Header Description

| Parameter | Type | Description |
| --- | --- | --- |
| Authorization | String | token |

### Request parameters

| Parameter | Type | Length | Description | Mandatory | constraint |
| --- | --- | --- | --- | --- | --- |
| userToken | String |  | User token | yes |  |
| userType | String | 2 | User Type | no | 0- end-user<br>1- agent |
| siteId | String | 10 | Site ID | yes |  |

### Response Parameters

| Parameter | Type | Length | Description | Mandatory | constraint |
| --- | --- | --- | --- | --- | --- |
| energyStatus | String | 15 | Battery working status<br>-charging；<br>-disCharging<br>-idel |  |  |
| energyPower | BigDecimal |  | Bettery working power |  |  |
| energySoc | BigDecimal |  | Battery SoC |  |  |
| pvStatus | String | 15 | PV working status<br>-generating；<br>-offline |  | Under developing |
| pvPower | BigDecimal |  | PV generating power |  |  |
| powerGridStatus | String | 15 | Power grid working status<br>- importing<br>- exporting |  | Under developing |
| powerGridPower | BigDecimal |  | Power grid working power |  |  |
| loadStatus | String | 15 | Load working status<br>- consuming<br>- idel |  | Under developing |
| loadPower | BigDecimal |  | Load consuming power |  |  |
| chargingPileStatus | String | 15 | EV charger working status<br>- available<br>- EV：Charging |  |  |
| chargingPilePower | BigDecimal |  | EV charger charging power |  |  |
| timestamp | Long | 13 | Latest data update time |  |  |
| code | String |  | http/https response code<br>- 200 ok；<br>- 201 Created；<br>- 401 Unauthorized；<br>- 403 Forbidden；<br>- 404 Not Found |  |  |
| message | String |  | Message code<br>- SUCCESS；<br>- FAIL； |  |  |

### Example

```
   https://api.livoltek-portal.com:8081/hess/api/site/527/curPowerflow?userToken=1&userType=1
```

### Response example

```
{
    "code": " String ",
    "message": " String ",
    "data": {
        "pvStatus":" String ",
        "pvPower": " BigDecimal ",
        "powerGridStatus": " String ",
        "powerGridPower": " BigDecimal ",
        "loadStatus": " String ",
        "loadPower": " BigDecimal ",
        "energyStatus": " String ",
        "energyPower": " BigDecimal ",
        "energySoc": " BigDecimal ",
        "chargingPileStatus": " String ",
        "chargingPilePower": " BigDecimal ",
        "timestamp": " Long "
    }
}

{
    "code": " 200 ",
    "message": " SUCCESS ",
    "data": {
        "pvStatus": null,
        "pvPower": 0.006,
        "powerGridStatus": null,
        "powerGridPower": 0.0,
        "loadStatus": "idel",
        "loadPower": 0.0,
        "energyStatus": "disCharging",
        "energyPower": -0.156,
        "energySoc": 100.0,
        "chargingPileStatus": null,
        "chargingPilePower": null,
        "timestamp": 1655789700000
    }
}
```

## 16. Device generation or consumption

> Return device lifetime generation or consumption

> **URL**: /hess/api/device/{deviceId}/realElectricity

> **Method**: GET

> **Header**: Header: Authorization : token

### Header Description

| Parameter | Type | Description |
| --- | --- | --- |
| Authorization | String | token |

### Request parameters

| Parameter | Type | Length | Description | Mandatory | constraint |
| --- | --- | --- | --- | --- | --- |
| userToken | String |  | User token | Yes |  |
| userType | String | 2 | User Type | no | 0- end-user<br>1- agent |
| deviceId | String | 10 | Device ID | yes |  |

### Response Parameters

| Parameter | Type | Length | Description | Mandatory | constraint |
| --- | --- | --- | --- | --- | --- |
| pvProduceElectric | String |  | Inver solar generation |  | kWh |
| loadCustomerElectric | String |  | load consumptions (only when there is RS485 meter connected to inverter) |  | kWh |
| timestamp | Long | 13 | Latest data update time |  | Online: return time;<br>Offline: return NULL |
| code | String |  | http/https response code<br>- 200 ok；<br>- 201 Created；<br>- 401 Unauthorized；<br>- 403 Forbidden；<br>- 404 Not Found |  |  |
| message | String |  | Message code<br>- SUCCESS；<br>- FAIL； |  |  |

### Example

```
   https://api.livoltek-portal.com:8081/hess/api/device/22018/realElectricity?userToken=1&userType=1
```

### Response example

```
{
    "code": " String ",
    "message": " String ",
    "data": {
        "loadCustomerElectric": "String",
        "pvProduceElectric": " String"
        "timestamp": " Long"
    }
}

{
    "code": "200",
    "message": "SUCCESS",
    "data": {
        "loadCustomerElectric": "3.1",
        "pvProduceElectric": "137.5",
        “timestamp”: 1655769319674
    }
}
```

## 17. Site Details

> return details of the selected site, including site id, site name, site image, installation region, installation time zone and so on

> **URL**: /hess/api/site/{siteId}/details**Method**: GET**Header**: Header: Authorization : token

### Header Description

| Parameter | Type | Description |
| --- | --- | --- |
| Authorization | String | token |

### Request parameters

| Parameter | Type | Length | Description | Mandatory | constraint |
| --- | --- | --- | --- | --- | --- |
| siteId | String |  | Site ID | yes |  |
| userToken | String |  | User token | yes |  |
| userType | String | 2 | User Type | no | 0- end-user<br>1- agent |

### Response Parameters

| Parameter | Type | Length | Description | Mandatory | constraint |
| --- | --- | --- | --- | --- | --- |
| powerStationId | String | 10 | Site ID |  |  |
| powerStationName | String | 64 | Site name |  |  |
| country | String | 255 | County/Region |  |  |
| timezone | String | 255 | time zone |  |  |
| administrativeRegion | String | 255 | administrative division |  | Under developing |
| powerStationType | String | 255 | Site type<br>1-Grid-tied solar system<br>2-Solar storage system<br>3-EV charging hub<br>4-EV charging hub with solar storage |  |  |
| powerStationStatus | Integer | 2 | Site communication status<br>1-all devices are online， |  |  |
|  |  |  | 2-all devices are offline，<br>3-some devices in this site are offline， |  |  |
| pvCapacity | String | 14 | PV capacity |  | Unit: kWp, GWp |
| registrationTime | Timestamp | 13 | The time when this site is being added to the system |  |  |
| updateTime | Long | 13 | The time for latest update of device in this site |  |  |
| active | Integer | 1 | If the site is active<br>0- not active<br>1- active |  |  |
| hasAlarm | Integer | 1 | Is the site with alarming device?<br>0- No<br>1- Yes |  | Under developing |
| siteIamge | String |  | Image uri of this site |  | Under developing |
| message | string | 64 | Message code<br>- SUCCESS；<br>- FAIL； |  |  |
| code | String | 10 | http/https response code<br>- 200 ok；<br>- 201 Created；<br>- 401 Unauthorized；<br>- 403 Forbidden；<br>- 404 Not Found |  |  |

### Example

```
   https://api.livoltek-portal.com:8081/hess/api/site/123/details?userToken=1&userType=1
```

### Response example

```
{
    "code": " String ",
    "message": " String ",
    "data": {
        "powerStationId": " String ",
        "powerStationName": " String ",
        "country": " String ",
        "timeZone": " String ",
        "administrativeRegion": " String ",
        "powerStationType": " String ",
        "powerStationStatus": " String ",
        "pvCapacity": " String ",
        "registrationTime": "Timestamp",
        "updateTime": “Long”,
        "active": " Integer ",
        "hasAlarm": " Integer ",
        "siteIamge": " String "
    }
}

{
    "code": "200",
    "message": "SUCCESS",
    "data": {
        "powerStationId": "3",
        "powerStationName": "test",
        "country": "CN",
        "timeZone": "Asia/Shanghai",
        "administrativeRegion": "CN",
        "powerStationType": "光伏并网系统",
        "powerStationStatus": "3",
        "pvCapacity": "322.0",
        "registrationTime": "2020-11-30T03:11:02.000+0000",
        "updateTime": 1655769319674,
        "active": 1,
        "hasAlarm": null,
        "siteIamge": null
    }
}
```

## 18. Site Installer

> return the installer company of the selected site

> **URL**: /hess/api/site/{siteId}/siteInstaller**Method**: get**Header**: Header: Authorization : token

### Header Description

| Parameter | Type | Description |
| --- | --- | --- |
| Authorization | String | token |

### Request parameters

| Parameter | Type | Length | Description | Mandatory | constraint |
| --- | --- | --- | --- | --- | --- |
| userToken | String |  | User token | yes |  |
| userType | String | 2 | User Type | no | 0- end-user<br>1- agent |
| siteId | String | 10 | Site ID | yes |  |

### Response Parameters

| Parameter | Type | Length | Description | Mandatory | constraint |
| --- | --- | --- | --- | --- | --- |
| installer | String | 128 | Installer company name of the selected site |  |  |
| orgCode | String |  | Installation vendor organization code |  |  |
| message | string | 64 | Message code<br>- SUCCESS<br>- FAIL； |  |  |
| code | String | 64 | http/https response code<br>- 200 ok；<br>- 201 Created；<br>- 401 Unauthorized；<br>- 403 Forbidden；<br>- 404 Not Found |  |  |

### Example

```
   https://api.livoltek-portal.com:8081/hess/api/site/123/siteInstaller?userToken=1&userType=1
```

### Response example

```
{
    "code": " String ",
    "message": " String ",
    "data": {
        "installer": " String ",
         " orgCode": " String "
    }
}

{
    "code": "200",
    "message": "SUCCESS",
    "data": {
        "installer": "perm001",
        "orgCode": "CN002U39FH"
    }
}
```

## 19. Site generation overview

> Return generation review of selected site, including site name，amount of online equipment, latest updated timestamp, power, daily generation, monthly generation, yearly generation, lifetime generation,

> **URL**: /hess/api/site/{siteId}/overview**Method**: GET**Header**: Header: Authorization : token

### Header Description

| Parameter | Type | Description |
| --- | --- | --- |
| Authorization | String | token |

### Request parameters

| Parameter | Type | Length | Description | Mandatory | constraint |
| --- | --- | --- | --- | --- | --- |
| userToken | String |  | User token | yes |  |
| userType | String | 2 | User Type | no | 0- end-user<br>1- agent |
| siteId | String | 10 | Site ID | yes |  |

### Response Parameters

| Parameter | Type | Length | Description | Mandatory | constraint |
| --- | --- | --- | --- | --- | --- |
| name | String | 64 | Site name |  |  |
| onlineDevice | String | 256 | Amount of online equipment |  |  |
| updateTime | String | 13 | Latest updated timestamp |  |  |
| currentPower | String | 256 | Real-time power |  | Unit: kW |
| eoutDaily | String | 256 | Daily generation |  | Unit: kWh |
| eoutMonth | String | 256 | Monthly generation |  | Unit: kWh |
| eoutCurrentYear | String | 256 | Annual generation |  | Unit: kWh |
| eTotalToGrid | String | 256 | Lifetime generation |  | Unit: kWh |
| message: | string | 64 | Message code<br>- SUCCESS<br>- FAIL； |  |  |
| code | String | 10 | http/https response code<br>- 200 ok；<br>- 201 Created；<br>- 401 Unauthorized；<br>- 403 Forbidden；<br>- 404 Not Found |  |  |

### Example

```
   https://api.livoltek-portal.com:8081/hess/api/site/123/overview?userToken=1&userType=1
```

### Response example

```
{
    "code": " String ",
    "message": " String ",
    "data": {
        "id": " String ",
        "name": " String ",
        "onlineDevice": "String",
        "currentPower": " String ",
        "eoutCurrentYear": " String",
        "eoutDaily": " String ",
        "eoutMonth": " String ",
        "updateTime": " Sting ",
        "etotalToGrid": " String "
    }
}

{
    "code": "200",
    "message": "SUCCESS",
    "data": {
        "id": "3",
        "name": "test",
        "onlineDevice": "1",
        "currentPower": "0.0",
        "eoutCurrentYear": "22493.575",
        "eoutDaily": "62.693",
        "eoutMonth": "2849.941",
        "updateTime": "1655769319674",
        "etotalToGrid": "22493.575"
    }
}
```

## 20. Site Historical Power Flow

> Query the energy flow of the specified site to obtain the update timestamp, status of each system type, parameter unit (W) and value in selected time duration:

- Photovoltaic working state (generating, offline) and power value,
- Working state of power grid (importing, exporting) and power value,
- Load working state ( consuming, idel) and power value,
- Energy storage working state (charging, discharging, idel), power and SOC.
- Working state of charger (available, EV charging) and power value

> Reques by site ID. and time duration<br>*When there is no internal and external electricity meter connected in the system, there is no return value of the power grid.<br>*start time should be within recent 7 days.

> **URL**: /hess/api/site/{siteId}/HisPowerflow**Method**: GET**Header**: Header: Authorization : token

### Header Description

| Parameter | Type | Description |
| --- | --- | --- |
| Authorization | String | token |

### Request parameters

| Parameter | Type | Length | Description | Mandatory | constraint |
| --- | --- | --- | --- | --- | --- |
| userToken | String |  | User token | yes |  |
| userType | String | 2 | User Type | no | 0- end-user<br>1- agent |
| siteId | String |  | Site ID | yes |  |
| pointInterval | Integer |  | Sampling accuracy<br>0- Every 5 minutes<br>1- Every 10 minutes(default)（No）<br>2- Every 15 minutes（No） | yes |  |
| startTime | Long |  | Start time for query, which should be in recent 7 days | yes | Timestamp:13 |
| endTime | Long |  | End up time for query | yes |  |

### Response Parameters

| Parameter | Type | Length | Description | Mandatory | constraint |
| --- | --- | --- | --- | --- | --- |
| energyStatus | String | 64 | Battery working status<br>- charging；<br>- disCharging<br>- idel |  |  |
| energyPower | String | 10 | Bettery working power |  | Unit: kW |
| energySoc | String | 64 | Battery SoC |  | Unit: % |
| pvStatus | String | 265 | PV working status<br>-generating；<br>-offline |  | Under developing |
| pvPower | String | 265 | PV generating power |  | Unit: kW |
| powerGridStatus | String | 64 | Power grid working status<br>- Importing<br>- exporting |  |  |
| powerGridPower | String | 265 | Power grid working power |  | Unit: kW |
| loadStatus | String | 64 | Load working status<br>- consuming<br>- idel |  |  |
| loadPower | String | 265 | Load consuming power |  | Unit: kW |
| chargingPileStatus | String | 64 | EV charger working status<br>- available<br>- EV：Charging |  | Under developing |
| chargingPilePower | String | 265 | EV charger charging power |  | Unit: kW<br>Under developing |
| timestamp | Long | 13 | Timestamp of data updating |  |  |
| message | String | 265 | Message code<br>- SUCCESS <br>- FAIL； |  |  |
| code | String | 13 | http/https response code<br>- 200 ok；<br>- 201 Created；<br>- 401 Unauthorized；<br>- 403 Forbidden；<br>- 404 Not Found |  |  |

### Example

```
   https://api.livoltek-portal.com:8081/hess/api/site/123/HisPowerflow?pointInterval =1&startTime=1659710500000&endTime=1659750500000&userType=1
```

### Response example

```
{
    "code": " String ",
    "message": " String ",
    "data": {
        "Long": [
            {
                "pvStatus": “String”,
                "pvPower": " String ",
                "powerGridStatus": “String”,
                "powerGridPower": " String ",
                "loadStatus": " String ",
                "loadPower": " String ",
                "energyStatus": " String ",
                "energyPower": " String ",
                "energySoc": " String ",
                "chargingPileStatus": “String”,
                "chargingPilePower": “String”,
                "timestamp": “Long”
            }
        ]
    }
}

{
    "code": "200",
    "message": "SUCCESS",
    "data": {
        "1655510400000": [
            {
                "pvStatus": null,
                "pvPower": "2.953",
                "powerGridStatus": "Importing",
                "powerGridPower": "2.743",
                "loadStatus": "consuming",
                "loadPower": "0.061",
                "energyStatus": "idel",
                "energyPower": "0.0",
                "energySoc": "100.0",
                "chargingPileStatus": null,
                "chargingPilePower": null,
                "timestamp": 1655510400000
            }
        ]
    }
}
```

## 21. Site Historical Active Power

> Query the historical power of the specified site to obtain the update timestamp, power value and unit (W) in selected time duration<br>*start time should be within recent 7 days.

> **URL**: /hess/api/site/{siteId}/power**Method**: GET**Header**: Header: Authorization : token

### Header Description

| Parameter | Type | Description |
| --- | --- | --- |
| Authorization | String | token |

### Request parameters

| Parameter | Type | Length | Description | Mandatory | constraint |
| --- | --- | --- | --- | --- | --- |
| userToken | String |  | User token | yes |  |
| userType | String | 2 | User Type | no | 0- end-user<br>1- agent |
| siteId | String |  | Site ID | yes |  |
| pointInterval | Integer |  | Sampling accuracy<br>0- Every 5 minutes<br>1- Every 10 minutes（No）<br>2- Every 15 minutes（No） | yes |  |
| startTime | Long |  | Start time for query, which should be in recent 7 days | yes |  |
| endTime | Long |  | End up time for query | yes |  |

### Response Parameters

| Parameter | Type | Length | Description | Mandatory | constraint |
| --- | --- | --- | --- | --- | --- |
| power | String | 64 | Power generation of the updated time |  | Unit: kW |
| timestamp | Long | 10 | Timestamp of data updating |  |  |
| message | String | 2566 | Message code<br>- SUCCESS <br>- FAIL； |  |  |
| code | String | 13 | http/https response code<br>- 200 ok；<br>- 201 Created；<br>- 401 Unauthorized；<br>- 403 Forbidden；<br>- 404 Not Found |  |  |

### Example

```
   https://api.livoltek-portal.com:8081/hess/api/site/123/power?pointInterval =1&startTime=1659102500000&endTime=1659202500000&userType=1
```

### Response example

```
{
    "code": " String ",
    "message": " String ",
    "data": {
        "Long": [
            {
                "power": “String”,
                "timestamp": “Long”
            },
        ]
    }
}

{
    "code": "200",
    "message": "SUCCESS",
    "data": {
        "1655510400000": [
            {
                "power": "100.0",
                "timestamp": 1655510400000
            },
        ]
    }
}
```

## 22. Device Historical Alarm

> Search device alarm logs in recent 7 days by device SN.

> **URL**: /hess/api/device/{siteId}/{serialNumber}/alarm**Method**: GET**Header**: Header: Authorization : token

### Header Description

| Parameter | Type | Description |
| --- | --- | --- |
| Authorization | String | token |

### Request parameters

| Parameter | Type | Length | Description | Mandatory | constraint |
| --- | --- | --- | --- | --- | --- |
| userToken | String |  | User token | yes |  |
| userType | String | 2 | User Type | no | 0- end-user<br>1- agent |
| siteId | String |  | Site ID | yes |  |
| serialNumber | Integer |  | Device SN | yes |  |
| size | Integer |  | Pagesize of each page,<br>-5<br>-10 (default)<br>-30 | yes |  |
| page | Integer |  | The first site index to be returned in the results, default=0 | yes |  |
| startTime | String |  | Start time for query, which should be in recent 7 days | yes | e.g. 2022-01-01 |
| endTime | String |  | End up time for query | yes | e.g. 2022-01-07 |

### Response Parameters

| Parameter | Type | Length | Description | Mandatory | constraint |
| --- | --- | --- | --- | --- | --- |
| alarmEvent | String | 1024 | Alarm code |  | For internal use |
| alarmStatus | String | 32 | Alarm Status （No）<br>- Active<br>- inactive |  | Under developing |
| alarmCode | String | 256 | Alarm code |  |  |
| alarmName | String | 256 | Alarm description, such as “AC Voltage High” |  |  |
| alarmType | String | 32 | Alarm type:<br>- Notice<br>- fault |  |  |
| originTime | Long | 13 | - Alarm timestamp |  |  |
| deviceType | String | 32 | - Device type |  |  |
| code | String |  | http/https response code<br>- 200 ok；<br>- 201 Created；<br>- 401 Unauthorized；<br>- 403 Forbidden；<br>- 404 Not Found |  |  |
| message | String |  | Message code<br>- SUCCESS；<br>- FAIL； |  |  |
| count | Integer |  |  |  |  |

### Example

```
  https://api.livoltek-portal.com:8081/hess/api/site/123/SN10203/alarm?startTime=2022-01-01&endTime=2022-01-07&page=1&size=10&userToken=*****&userType=1
```

### Response example

```
{
    "code": " String ",
    "message": " String ",
    "data": {
        "list": [
            {
                "alarmCode": " String ",
                "alarmName": " String ",
                "alarmEvent": " String ",
                "alarmStatus": “String”,
                "alarmType": " String ",
                "originTime": “Long”,
                "deviceType": " String "
            }
        ],
        "count": “Integer”
    }
}

{
    "code": "200",
    "message": "SUCCESS",
    "data": {
        "list": [
            {
                "alarmCode": "Grid voltage high action(0.0 0.0 0.0 0.00 0.00 0.00 208.0 117.8 0.0 0.0 0 0 0)",
                "alarmName": "Grid AC over voltage",
                "alarmEvent": "Grid AC over voltage",
                "alarmStatus": null,
                "alarmType": "0",
                "originTime": 1655757708000,
                "deviceType": "2_19"
            }
        ],
        "count": 1
    }
}
```

## 23. Site Social Contribution

> Return site social contribution of last update time, CO2 reduce, Equivalent tree planting and standard coal reduced.

> **URL**: /hess/api/site/{siteId}/socialContr**Method**: GET**Header**: Header: Authorization : token

### Header Description

| Parameter | Type | Description |
| --- | --- | --- |
| Authorization | String | token |

### Request parameters

| Parameter | Type | Length | Description | Mandatory | constraint |
| --- | --- | --- | --- | --- | --- |
| userToken | String |  | User token | Yes |  |
| userType | String | 2 | User Type | no | 0- end-user<br>1- agent |

### Response Parameters

| Parameter | Type | Length | Description | Mandatory | constraint |
| --- | --- | --- | --- | --- | --- |
| date | Long | 13 | Latest data update time |  |  |
| savingCO2 | String | 32 | CO2 reduce |  | tons |
| savingTree | String | 32 | Equivalent tree planting |  | Pieces |
| savingCoal | String | 32 | standard coal reduce |  | tons |
| code | String |  | http/https response code<br>- 200 ok；<br>- 201 Created；<br>- 401 Unauthorized；<br>- 403 Forbidden；<br>- 404 Not Found |  |  |
| message | String |  | Message code<br>- SUCCESS；<br>- FAIL； |  |  |

### Example

```
  https://api.livoltek-portal.com:8081/hess/api/site/{siteId}/socialContr?userToken=1&userType=1
```

### Response example

```
{
    "code": " String ",
    "message": " String ",
    "data": {
        "savingCoal": " String ",
        "savingCO2": " String ",
        "savingTree": " String ",
        "date": "Long"
    }
}

{
    "code": "200",
    "message": "SUCCESS",
    "data": {
        "savingCoal": "17658.69",
        "savingCO2": "22427.67",
        "savingTree": "3509.24",
        "date": "1655769319674"
    }
}
```

## 24. Storage Information

> Query the information of the energy storage battery in the specified site to obtain the BAT capacity, BMS SN, current SOC/voltage, battery type, and power / voltage / SOC in recent 7 days, and daily charge and discharge capacity in recent 7 days.

> **URL**: hess/api/site/{siteId}/ESS**Method**: GET**Header**: Header: Authorization : token

### Header Description

| Parameter | Type | Description |
| --- | --- | --- |
| Authorization | String | token |

### Request parameters

| Parameter | Type | Length | Description | Mandatory | constraint |
| --- | --- | --- | --- | --- | --- |
| userToken | String |  | User token | yes |  |
| userType | String | 2 | User Type | no | 0- end-user<br>1- agent |
| siteId | String |  | Site ID | yes |  |

### Response Parameters

| Parameter | Type | Length | Description | Mandatory | constraint |
| --- | --- | --- | --- | --- | --- |
| message | string |  | Message code<br>- SUCCESS；<br>- FAIL； |  |  |
| code | Int |  | http/https response code<br>- 200 ok；<br>- 201 Created；<br>- 401 Unauthorized；<br>- 403 Forbidden<br>- 404 Not Found |  |  |
| BMSCapacity | String | 20 | Battery Capacity (from BMS) |  | Unit：Ah |
| batterySn | String | 32 | BMS SN |  | underdeveloping |
| cycleCount | Integer | 20 | Battery cycle count |  | underdeveloping |
| deviceId | Integer | 32 | Device ID of BMS |  |  |
| deviceSn | String | 32 | Serial number of BMS |  |  |
| batteryType | String | 20 | Battery Type<br>0：No battery<br>1：LIVOLTEK Low voltage lithium battery<br>2：Lithium<br>3：Other Li-ion without BMS<br>4：LFP15 without BMS<br>5：LFP16 without BMS<br>10：AGM<br>11：FLD<br>12：USER<br>13：Li2<br>14：Li4<br>100: Lead-acid(AGM/Flooded/Gel)<br>101：LIVOLTEK |  |  |
| energyPower | String | 20 | Battery power |  |  |
| energySoc | String | 20 | Battery SoC |  |  |
| energyVolage | String | 20 | Battery voltage |  |  |
| charge | String | 20 | Charging energy |  |  |
| discharge | String | 20 | Discharging energy |  |  |
| time | Long | 20 | Time stamp |  | Unit: ms |

### Example

```
   https://api.livoltek-portal.com:8081/hess/api/site/527/ESS?userToken=1&userType=1
```

### Response example

```
{ "data": {
        " BMSCapacity ": " String ",
        "batterySn": " String ",
        "currentSoc": " String ",
        "cycleCount": " Integer ",
        "batteryTypeList": [
            {
                "deviceId": “Integer”,
                "deviceSn":  " String ",
                "batteryType":  " String "
            }
        ],
        "historyMap": {
           "timestamp：Long": [
                {
                    "energyPower":  " String ",
                    "energySoc":  " String ",
                    "energyVolage":  " String ",
                    "charge":  " String ",
                    "discharge":  " String ",
                    "time": “Long”
                }
}
} 
，  
  " message ": "string",
  " code ": "string",
}
{
    "code": "200",
    "message": "SUCCESS",
    "data": {
        " BMSCapacity ": "1111.0",
        "batterySn": null,
        "currentSoc": "0",
        "cycleCount": null,
        "batteryTypeList": [
            {
                "deviceId": 195,
                "deviceSn": "test-42-GF3k0003",
                "batteryType": null
            },
            {
                "deviceId": 199,
                "deviceSn": "1234567890121212",
                "batteryType": null
            }
        ],
        "historyMap": {
            "1657584000000": [
                {
                    "energyPower": null,
                    "energySoc": null,
                    "energyVolage": null,
                    "charge": null,
                    "discharge": null,
                    "time": 1657584000000
                }
}
} 
}
```

## 25. Device Details

> Query the equipment information of the specified device to obtain the device model, SN, working condition (offline, normal, fault, etc.) and its update time, firmware version, device type and manufacturer.

> **URL**: hess/api/device/{siteId}/{serialNumber}/details**Method**: GET**Header**: Header: Authorization : token

### Header Description

| Parameter | Type | Description |
| --- | --- | --- |
| Authorization | String | token |

### Request parameters

| Parameter | Type | Length | Description | Mandatory | constraint |
| --- | --- | --- | --- | --- | --- |
| userToken | String |  | User token | yes |  |
| userType | String | 2 | User Type | no | 0- end-user<br>1- agent |
| siteId | String |  | Site ID | Yes |  |
| serialNumber | String |  | Device serial number | yes |  |

### Response Parameters

| Parameter | Type | Length | Description | Mandatory | constraint |
| --- | --- | --- | --- | --- | --- |
| message | String |  | Message code<br>- SUCCESS；<br>- FAIL； |  |  |
| code | String |  | http/https response code<br>- 200 ok；<br>- 201 Created；<br>- 401 Unauthorized；<br>- 403 Forbidden；<br>- 404 Not Found |  |  |
| id | Integer | 64 | Device ID |  |  |
| productType | String | 20 | Product Type |  |  |
| inverterSn | String | 64 | Device serial number |  |  |
| collectorSn | String | 64 | Device serial number |  | Under developing |
| runningStatus | String | 10 | Device Runing status<br>0：Normal<br>1：Standby<br>2：Fault<br>3：Offline<br>4：Self-test<br>5：Upgrading |  |  |
| updateTime | Long | 32 | Last update time |  | Unit: ms |
| firmwareVersion | String | 32 | Firmware version |  |  |
| deviceType | String | 64 | Device type: inverter(default) |  |  |
| deviceManufacturer | String | 64 | manufacturer |  | Livoltek<br>(default) |

### Example

```
   https://api.livoltek-portal.com:8081/hess/api/device/527/SN123456/details?userToken=1&userType=1
```

### Response example

```
 {
    "code": " String ",
    "message": " String ",
    "data": {
        "id": “Integer”,
        " productType ":" String ",
        "inverterSn":" String ",
        "collectorSn":" String ",
        " runningStatusVoMap": {
            "timestamp：Long": [
                {
                    " runningStatus ": " String ",
                    "updateTime": “Long”
                }
]
        },
        "firmwareVersion": " String ",
        " deviceType ": " String ",
        "deviceManufacturer": " String ",
    }
}

 {
    "code": "200",
    "message": "SUCCESS",
    "data": {
        "id": null,
        " productType ": "inverter",
        "inverterSn": null,
        "collectorSn": null,
        " runningStatusVoMap ": {
            "1658102400000": [
                {
                    " runningStatus ": null,
                    "updateTime": 1658102400000
                }
]
        },
        "firmwareVersion": null,
        " deviceType ": null,
        "deviceManufacturer": "LIVOLTEK"
    }
}
```

## 26. Device technical parameters in recent 7 days

> Query the real-time technical parameter data of the specified equipment to obtain the real-time data of the corresponding equipment, data update time and value, including the current / voltage of each MPPT, the voltage / current of three-phase power grid, power grid frequency, active power of power grid, apparent power of power grid, etc. <br>*in recent 7 days.<br>*Data interval is 5 minutes.

> **URL**: hess/api/device/{siteId}/{serialNumber}/realTime**Method**: GET**Header**: Header: Authorization : token

### Header Description

| Parameter | Type | Description |
| --- | --- | --- |
| Authorization | String | token |

### Request parameters

| Parameter | Type | Length | Description | Mandatory | constraint |
| --- | --- | --- | --- | --- | --- |
| userToken | String |  | User token | yes |  |
| userType | String | 2 | User Type | no | 0- end-user<br>1- agent |
| siteId | String |  | Site ID | yes |  |
| serialNumber | String |  | Device serial number | yes |  |
| startTime | String |  | Start time | No | 2025-01-18 00:00:00 |
| endTime | String |  | End time | No | 2025-01-18 23:59:59 |

### Response Parameters

| Parameter | Type | Length | Description | Mandatory | constraint |
| --- | --- | --- | --- | --- | --- |
| message | String |  | Message code<br>- SUCCESS；<br>- FAIL； |  |  |
| code | String |  | http/https response code<br>- 200 ok；<br>- 201 Created；<br>- 401 Unauthorized；<br>- 403 Forbidden；<br>- 404 Not Found |  |  |
| p1Voltage | String | 20 | Voltage of PV1 |  |  |
| p1Current | String | 20 | Current of PV1 |  |  |
| p2Voltage | String | 20 | Voltage of PV2 |  |  |
| p2Current | String | 20 | Current of PV2 |  |  |
| p3Voltage | String | 20 | Voltage of PV3 |  |  |
| p3Current | String | 20 | Current of PV3 |  |  |
| p4Voltage | String | 20 | Voltage of PV4 |  |  |
| p4Current | String | 20 | Current of PV4 |  |  |
| p5Voltage | String | 20 | Voltage of PV5 |  |  |
| p5Current | String | 20 | Current of PV5 |  |  |
| p6Voltage | String | 20 | Voltage of PV6 |  |  |
| p6Current | String | 20 | Current of PV6 |  |  |
| p7Voltage | String | 20 | Voltage of PV7 |  |  |
| p7Current | String | 20 | Current of PV7 |  |  |
| p8Voltage | String | 20 | Voltage of PV8 |  |  |
| p8Current | String | 20 | Current of PV8 |  |  |
| p9Voltage | String | 20 | Voltage of PV9 |  |  |
| p9Current | String | 20 | Current of PV9 |  |  |
| p10Voltage | String | 20 | Voltage of PV10 |  |  |
| p10Current | String | 20 | Current of PV10 |  |  |
| p11Voltage | String | 20 | Voltage of PV11 |  |  |
| p11Current | String | 20 | Current of PV11 |  |  |
| p12Voltage | String | 20 | Voltage of PV12 |  |  |
| p12Current | String | 20 | Current of PV12 |  |  |
| rVoltage | String | 20 | Phase A voltage of inverter AC interface |  |  |
| rCurrent | String | 20 | PhaseB voltage of inverter AC interface |  |  |
| sVoltage | String | 20 | Phase C voltage of inverter AC interface |  |  |
| sCurrent | String | 20 | Phase A current of inverter AC interface |  |  |
| tVoltage | String | 20 | Phase B current of inverter AC interface |  |  |
| tCurrent | String | 20 | Phase C current e of inverter AC interface |  |  |
| dwActivePower | String | 20 | Grid active power |  |  |
| dwApparentPower | String | 20 | Grid apparent power |  |  |
| girdFrequency | String | 20 | Grid frequency |  |  |
| batteryVoltage | String | 20 | BMS voltage |  |  |
| batteryCurrent | String | 20 | BMS current |  |  |
| batterySoc | String | 20 | BMS SoC |  |  |
| epsCurrent | String | 20 | EPS current (apply for hybrid) |  |  |
| epsVoltage | String | 20 | EPS voltage (apply for hybrid) |  |  |
| epsFrequency | String | 20 | EPS frequency (apply for hybrid) |  |  |
| timestamp | Long | 20 | timestamp |  |  |

### Example

```
   https://api.livoltek-portal.com:8081/hess/api/device/527/SN123456/realTime?userToken=1&userType=1 &startTime=2025-01-18 00:00:00&endTime=2025-01-18 23:59:59
   https://api-eu.livoltek-portal.com:8081/hess/api/device/527/SN123456/realTime?userToken=1&userType=1 &startTime=2025-01-18 00:00:00&endTime=2025-01-18 23:59:59
```

### Response example

```
{
    "code": " String",
    "message": " String ",
    "data": {
        "timestamp：Long": [
            {
                "p1Voltage": " String",
                "p1Current": " String",
                "p2Voltage": " String",
                "p2Current": " String",
                "p3Voltage": " String",
                "p3Current":" String",
                "p4Voltage":" String",
                "p4Current": " String",
                "p5Voltage":" String",
                "p5Current": " String",
                "p6Voltage": " String",
                "p6Current": " String",
                "p7Voltage": " String",
                "p7Current": " String",
                "p8Voltage": " String",
                "p8Current": " String",
                "p9Voltage": " String",
                "p9Current": " String",
                "p10Voltage":" String",
                "p10Current": " String",
                "p11Voltage": " String",
                "p11Current": " String",
                "p12Voltage": " String",
                "p12Current": " String",
                "dwActivePower": " String",
                "dwApparentPower": " String",
                "girdFrequency":" String",
                "batteryVoltage": " String",
                "batteryCurrent": " String",
                "batterySoc": " String",
                "epsCurrent":" String",
                "epsVoltage": " String",
                "epsFrequency": " String",
                "timestamp": “Long”,
                "rvoltage":" String",
                "svoltage": " String",
                "tvoltage":" String",
                "rcurrent": " String",
                "scurrent":" String",
                "tcurrent": " String",
            }
        ]
    }
}

{
    "code": "200",
    "message": "SUCCESS",
    "data": {
        "1657756800000": [
            {
                "p1Voltage": null,
                "p1Current": null,
                "p2Voltage": "1000",
                "p2Current": null,
                "p3Voltage": null,
                "p3Current": null,
                "p4Voltage": null,
                "p4Current": null,
                "p5Voltage": null,
                "p5Current": null,
                "p6Voltage": null,
                "p6Current": null,
                "p7Voltage": null,
                "p7Current": null,
                "p8Voltage": null,
                "p8Current": null,
                "p9Voltage": null,
                "p9Current": null,
                "p10Voltage": null,
                "p10Current": null,
                "p11Voltage": null,
                "p11Current": null,
                "p12Voltage": null,
                "p12Current": null,
                "dwActivePower": null,
                "dwApparentPower": null,
                "girdFrequency": null,
                "batteryVoltage": null,
                "batteryCurrent": null,
                "batterySoc": null,
                "epsCurrent": null,
                "epsVoltage": null,
                "epsFrequency": null,
                "timestamp": 152988938059000,
                "rvoltage": null,
                "svoltage": null,
                "tvoltage": null,
                "rcurrent": null,
                "scurrent": null,
                "tcurrent": null
            }
        ],
        "1657584000000": [],
        "1657843200000": [],
        "1658016000000": [],
        "1658102400000": [],
        "1657670400000": [],
        "1657929600000": [],
        "1657497600000": []
    }
}
```

## 27. Site historical solar generation in recent 2 years

> Query for site historical solar generation in specific time interval, including every day’s generation in the specified time period, with the unit of daily / weekly / monthly<br>*Limit: 1)When the unit is day / week, the start and end time should be within the past two years, <br>2)the interval (from start to end time)should not exceed 31 days with the unit “ day”, <br>3)the interval should not exceed 180 days with the unit “week”;

> **URL**: hess/api /site/{siteId}/solarEnergy**Method**: GET**Header**: Header: Authorization : token

### Header Description

| Parameter | Type | Description |
| --- | --- | --- |
| Authorization | String | token |

### Request parameters

| Parameter | Type | Length | Description | Mandatory | constraint |
| --- | --- | --- | --- | --- | --- |
| userToken | String |  | User token | Yes |  |
| userType | String | 2 | User Type | no | 0- end-user<br>1- agent |
| siteId | String | 32 | Site ID | Yes |  |
| startTime | String | 8 | Start time | Yes | e.g.20220726 |
| endTime | String | 8 | End time | Yes | e.g.20220726 |
| timeType | String | 2 | Time interval type<br>0：day<br>1: week<br>2: month<br>3: year | yes |  |
| page | Int |  | The first site index to be returned in the results, default=1 | yes |  |
| size | Int |  | Pagesize of each page,<br>- 5<br>-10 (default)<br>-30 | yes |  |

### Response Parameters

| Parameter | Type | Length | Description | Mandatory | constraint |
| --- | --- | --- | --- | --- | --- |
| message | String | 10 | Message code<br>- SUCCESS；<br>- FAIL； |  |  |
| code | String | 10 | http/https response code<br>- 200 ok；<br>- 201 Created；<br>- 401 Unauthorized；<br>- 403 Forbidden；<br>- 404 Not Found |  |  |
| siteId | String | 32 | Site ID |  |  |
| powerGeneration | String | 32 | olar generation |  |  |
| ts | String | 20 | Date |  | timeType = 0,e.g.20220301<br>timeType = 1,e.g.20220301~20220307<br>timeType = 2,,e.g.202203<br>timeType = 3,,e.g.2022 |

### Example

```
  https://api.livoltek-portal.com:8081/hess/api/site/527/SN123456？userToken=1&startTime=20220726&endTime=20220726&timeType=3&userType=1&page=1&size=10
```

### Response example

```
{
    "code": " String ",
    "message": " String ",
    "data": {
        [{
            "siteId": "siteId",
            "powerGeneration":"String",
            "ts":"String"
        }]
    }
}
{
    "code": "200",
    "message": "SUCCESS",
    "data": [
        {
            "siteId": "527",
            "ts": "20220701~20220703",
            " powerGeneration ": null
        },
        {
            "siteId": "527",
            "ts": "20220704~20220710",
            " powerGeneration ": null
        },
        {
            "siteId": "527",
            "ts": "20220711~20220717",
            " powerGeneration ": null
        },
        {
            "siteId": "527",
            "ts": "20220718~20220724",
            " powerGeneration ": "69.9"
        },
        {
            "siteId": "527",
            "ts": "20220725~20220730",
            " powerGeneration ": "25.0"
        }
    ]
}
```

## 28. Site historical grid import&export in recent 2 years

> Query the historical grid energy of the specified site, query the historical total solar generation(Wh), grid import energy(Wh), grid export energy(Wh) in the specified time period, with the unit of daily / weekly / monthly <br>*Limit: 1)When the unit is day / week, the start and end time should be within the past two years, <br>2)the interval (from start to end time)should not exceed 31 days with the unit “ day”, <br>3)the interval should not exceed 180 days with the unit “week”;

> **URL**: hess/api/site/{siteId}/utilityEnergy**Method**: GET**Header**: Header: Authorization : token

### Header Description

| Parameter | Type | Description |
| --- | --- | --- |
| Authorization | String | token |

### Request parameters

| Parameter | Type | Length | Description | Mandatory | constraint |
| --- | --- | --- | --- | --- | --- |
| userToken | String |  | User token | yes |  |
| userType | String | 2 | User Type | no | 0- end-user<br>1- agent |
| siteId | String | 32 | Site ID | yes |  |
| timeType | Integer | 2 | Time Type | yes | 0：day；1：week；2：month：3:year |
| startTime | String | 8 | Start Time | yes | format：yyyyMMdd |
| endTime | String | 8 | End Time | yes | format：yyyyMMdd<br>option，default(current day) |
| size | Integer |  | Size of one page | yes |  |
| page | Integer |  | Current page | yes |  |

### Response Parameters

| Parameter | Type | Length | Description | Mandatory | constraint |
| --- | --- | --- | --- | --- | --- |
| positive | String | 10 | Energy import from grid |  |  |
| negative | String | 10 | Energy export to grid |  |  |
| powerGeneration | String | 10 | Solar generation |  |  |
| ts | String | 20 | timestamp |  |  |
| siteId | String | 32 | Site id |  |  |
| message | String | 10 | Message code<br>- operate.success;<br>- operate.fail； |  |  |
| code | String | 10 | http/https request return code<br>- 200 ok；<br>- 201 Created；<br>- 401 Unauthorized；<br>- 403 Forbidden;<br>- 404 Not Found |  |  |

### Example

```
  https://api.livoltek-portal.com:8081/hess/api/site/123/utilityEnergy?timeType=1&startTime=20220701&endTime=20220731&size=10&page=1&userType
```

### Response example

```
 {
	"data":{
        “historyList”:[ {
            " positive ": " string ",
            " negetive ": " string ",
            " ts ": " string ",
            "siteId": " string ",

        }],
        "etotalToGrid": {
            "siteId": " string ",
            "ts": " string ",
            " powerGeneration ": " string "
        }

    },  
    "message": "string",
    "msgCode": "string",
}

{
    "code": "200",
    "message": "SUCCESS",
    "data": {
        "historyList": [
            {
                "siteId": "527",
                "ts": "20220724~20220725",
                "positive": "0.0",
                "negative": "0.0"
            }
        ],
        " etotalToGrid ": {
            "siteId": "527",
            "ts": "20220724~20220725",
            " powerGeneration ": "47.2"
        }
    }
}
```

## 29. API user login and get token

> Get api user token and verify whether the API caller has permission

> **URL**: hess/api /login**Method**: POST**Header**: Content-Type : application/json

### Header Description

### Request parameters

| Parameter | Type | Length | Description | Mandatory | constraint |
| --- | --- | --- | --- | --- | --- |
| secuid | String | 32 | Security ID | yes |  |
| key | String | 1024 | Securiity Key | yes |  |

### Response Parameters

| Parameter | Type | Length | Description | Mandatory | constraint |
| --- | --- | --- | --- | --- | --- |
| mssage | string |  | Message code |  | SUCCESS |
| code | string | 10 | http/https request code |  | 200 ok；<br>201 Created；<br>401 Unauthorized；<br>403 Forbidden；<br>404 Not Found |
| data | String | 1024 |  |  |  |
| msgCode | String | 10 |  |  | operate.success；<br>operate.fail； |
| messgae | tring | 10 |  |  |  |
| data | String | 1024 | token |  |  |
| msg_code | String | 10 |  |  | operate.success；<br>operate.fail； |

### Example

```
   https://api.livoltek-portal.com:8081/hess/api/login
  {
    "secuid":"String"
    "key":"String"
  }
```

### Response example

```
 {
    "code": " string ",
    "message": "SUCCESS",
    "data": {
        "msgCode": " string ",
        "message": string,
        "data": " string ",
        "msg_code": " string "
    }
}

{
    "code": "200",
    "message": "SUCCESS",
    "data": {
        "msgCode": "operate.success",
        "message": null,
        "data": "<token-de-ejemplo-omitido>",
        "msg_code": "operate.success"
    }
}
```

## 30. Charging station creation

> Create a charging station. This station belongs to the user who calls the interface currently. The type of power station can only be a charging station

> **URL**: /hess/api/chargeSite/create**Method**: POST**Header**: Header：Authorization : token

### Header Description

| Parameter | Type | Description |
| --- | --- | --- |
| Authorization | String | token |

### Request parameters

| Parameter | Type | Length | Description | Mandatory | note |
| --- | --- | --- | --- | --- | --- |
| userToken | String |  | User token | yes |  |
| userType | String | 2 | User Type | no | 0：end-user<br> 1：agent |
| account | String |  | user account | yes |  |
| pwd | String |  | User password encrypted using MD5 | yes |  |
| adress | String |  | Address of charging station | yes |  |
| countryValue | String |  | Country code | yes | e.g: CN |
| currencyUnitValue | String |  | Currency code | yes | e.g: $ |
| customer | Long |  | Consumer ID of the user | yes |  |
| downPrice | Object |  | Off grid electricity price | yes |  |
| price | Double |  | Off grid electricity price | yes |  |
| startTime | Long |  | time-on | yes | e.g: 0 |
| endTime | Long |  | End Time | yes | e.g: 86400 |
| gridTiedType | Integer |  | Grid connection type | yes | 1:100% feed-in<br> 2:self-use first<br> 3:0 feed-in<br> 4:Off-grid |
| isShown | Integer |  | Is the charging station visible to the consumer's user | yes | 0: invisible<br> 1: visible |
| latitude | Double |  | latitude | yes |  |
| longitude | Double |  | longitude | yes |  |
| name | String |  | Charging station name | yes |  |
| timezoneValue | String |  | Time zone where the charging station is located | yes | e.g: Asia/Shanghai |
| upPrice | Object |  | feed-in tariff | yes |  |
| price | Double |  | feed-in tariff | yes |  |
| startTime | Long |  | time-on | yes | e.g: 0 |
| endTime | Long |  | End Time | yes | e.g: 86400 |

### Response Parameters

| Parameter | Type | Length | Description | Mandatory | note |
| --- | --- | --- | --- | --- | --- |
| message | String |  | Message code<br>-SUCCESS<br>-FAIL |  |  |
| code | String |  | http/https response code<br>-200 ok<br>-201 Created<br>-401 Unauthorized<br>-403 Forbidden<br>-404 Not Found |  |  |

### Example

```
https://api.livoltek-portal.com:8081/hess/api/chargeSite/create? userToken=xxx&userType=1
https://api-eu.livoltek-portal.com:8081/hess/api/chargeSite/create? userToken=xxx&userType=1
{
  "account": "admin618",
  "adress": "China NanJing",
  "countryValue": "CN",
  "currencyUnitValue": "$",
  "customer": 26123546544,
  "downPrice": [
    {
      "endTime": 86400,
      "price": 12.3,
      "startTime": 0
    }
  ],
  "gridTiedType": 0,
  "isShown": 1,
  "latitude": 30,
  "longitude": 120,
  "name": "test",
  "pwd": "<md5-de-ejemplo-omitido>",
  "timezoneValue": "Asia/Shanghai",
  "upPrice": [
    {
      "endTime": 86400,
      "price": 2.3,
      "startTime": 0
    }
  ]
}
```

### Response example

```
{
    "code": "String",
    "message": "String",
}
{
    "code": "200",
    "message": "SUCCESS",
}
```

## 31. Charging station query

> According to the query criteria, query the power station information under the user's name

> **URL**: /hess/api/chargeSite/querySite**Method**: POST**Header**: Header：Authorization : token

### Header Description

| Parameter | Type | Description |
| --- | --- | --- |
| Authorization | String | token |

### Request parameters

| Parameter | Type | Length | Description | Mandatory | note |
| --- | --- | --- | --- | --- | --- |
| userToken | String |  | User token | yes |  |
| userType | String | 2 | User Type | no | 0：end-user 1：agent |
| account | String |  | user account | yes |  |
| pwd | String |  | User password encrypted using MD5 | yes |  |
| filterName | String |  | Charging station name | no |  |
| filterTime | List |  | Query by time list | no |  |
| page | Int |  | The first site index to be returned in the results, default=1 | yes |  |
| size | Int |  | Pagesize of each page, -5 -10 (default) -30 | yes |  |

### Response Parameters

| Parameter | Type | Length | Description | Mandatory | Note |
| --- | --- | --- | --- | --- | --- |
| message | String |  | Message code - SUCCESS； - FAIL； |  |  |
| code | String |  | http/ https response code<br> - 200 ok；<br> - 201 Created；<br> - 401 Unauthorized；<br> - 403 Forbidden；<br> - 404 Not Found |  |  |
| adress | String |  | Charging station address |  |  |
| agent | Integer |  | Agent ID |  |  |
| agentAndParent | List |  | Agent relationship |  |  |
| batteryCapacity | String |  | Battery capacity |  |  |
| batteryCapacityUnit | String |  | Battery capacity Unit |  |  |
| chargingCapacity | String |  | Charging station capacity |  |  |
| chargingType | Integer |  | Charging Station Type |  |  |
| chargingTypeName | String |  | Charging Station Model Name |  |  |
| codeName | String |  | Agent code |  |  |
| country | String |  | Country ID |  |  |
| countryName | String |  | Country name |  |  |
| countryValue | String |  | Country code |  |  |
| createSource | String |  | Create Source |  | 0：web <br> 1：Android<br> 2：ios<br> 3:api |
| creatorId | Integer |  | Creator ID |  |  |
| creatorType | Integer |  | Creator Type |  | 0:tob<br> 1:toc |
| currencySymbol | String |  | currency symbol |  |  |
| currencyUnit | Integer |  | Currency Unit ID |  |  |
| currencyUnitName | String |  | piastre |  |  |
| currencyUnitValue | String |  | Currency unit code |  |  |
| currentPower | String |  | Current power |  |  |
| customer | Integer |  | user id |  |  |
| customerName | String |  | User Name |  |  |
| downPrice | Object |  | Off grid electricity price |  |  |
| powerStation | Integer |  | Charging station ID |  |  |
| price | Double |  | Electricity price |  |  |
| startTime | Integer |  | time-on |  |  |
| id | Integer |  | Offline electricity price ID |  |  |
| endTime | Integer |  | End Time |  |  |
| gridTiedType | Integer |  | Grid connection type |  | 1：100% feed-in<br> 2：Self-use first<br> 3：0 feed-in<br> 4：Off-grid |
| id | Integer |  | Station ID |  |  |
| isShown | Integer |  | Is it visible |  | 0: invisible<br> 1: visible |
| latitude | Double |  | Latitude |  |  |
| longitude | Double |  | Longitude |  |  |
| name | String |  | Name of power station |  |  |
| no | String |  | Organization of the power station no |  |  |
| oldAgent | Integer |  | False agent ID when visible is not checked |  |  |
| orgCode | String |  | Agent code |  |  |
| productSeries | Integer |  | Product Family ID |  |  |
| productSeriesName | String |  | Series Name |  |  |
| pvArrange | Integer |  | PV array |  |  |
| pvCapacity | String |  | PV capacity |  |  |
| pvCapacityUnit | String |  | PV Capacity Unit |  |  |
| pvType | String |  | PV type |  |  |
| quarterReport | Integer |  | Quarterly report switch |  | 1: Open<br> 0: Close |
| quarterReportEmail | String |  | Quarterly report email |  |  |
| registrationTime | String |  | Registration time |  |  |
| registrationTimeZone | String |  | Registration time zone |  |  |
| series | String |  | Power Station Series |  |  |
| status | Integer |  | Station status |  | 1- Normal<br> 2- Disconnect |
| systemEfficiency | String |  | Power |  |  |
| systemType | Integer |  | System type |  | 3：Charging station |
| systemTypeName | String |  | System Type Name |  |  |
| timezone | Integer |  | Time zone ID |  |  |
| timezoneName | String |  | Time zone name |  |  |
| timezoneValue | String |  | Time zone value |  |  |
| todayPowerGeneration | String |  | Today's power generation |  |  |
| totalPowerGeneration | String |  | Total power generation |  |  |
| upPrice | Object |  | feed-in tariff |  |  |
| powerStation | Integer |  | Charging station ID |  |  |
| price | Double |  | Electricity price |  |  |
| startTime | Integer |  | time-on |  |  |
| id | Integer |  | Offline electricity price ID |  |  |
| updateTime | Integer |  | update time |  |  |
| updateTimeZone | String |  | Time zone name |  |  |
| workStatus | Integer |  | working condition |  |  |

### Example

```
https://api.livoltek-portal.com:8081/hess/api/chargeSite/querySite? userToken=xxx&userType=1
https://api-eu.livoltek-portal.com:8081/hess/api/chargeSite/querySite? userToken=xxx&userType=1
{
"account": "admin618",
"pwd": "<md5-de-ejemplo-omitido>",
	"filterName": "test",
	"filterTime": ["2023-04-30T16:00:00.000Z", "2023-05-29T15:59:59.000Z"],
	"page": 1,
	"size": 10
}
```

### Response example

```
{
	"code": " 200 ",
	"message": " success",
	"data":[
		{
			"adress":"China NanJin",
			"agent":238039445626880,
			"agentAndParent":[
				0,
				238039445626880
			],
			"batteryCapacity":null,
			"batteryCapacityUnit":"kWp",
			"chargingCapacity":null,
			"chargingType":null,
			"chargingTypeName":null,
			"codeName":"CN00HMLU1D(Autotester)",
			"country":45,
			"countryName":"China",
			"countryValue":null,
			"createSource":null,
			"creatorId":null,
			"creatorType":null,
			"currencySymbol":null,
			"currencyUnit":3,
			"currencyUnitName":"CNY, ￥",
			"currentPower":"0",
			"customer":169710293409792,
			"customerName":"tang",
			"downPrice":[
				{
					"endTime":86400,
					"id":757,
					"powerStation":620,
					"price":0.0,
					"startTime":0
				}
			],
			"energyStorages":null,
			"gridTiedType":1,
			"id":620,
			"image":null,
			"imageUrl":null,
			"isShown":1,
			"latitude":39.983813,
			"longitude":116.345813,
			"name":"testsite",
			"no":null,
			"oldAgent":238039445626880,
			"orgCode":"CN00HMLU1D",
			"productSeries":null,
			"productSeriesName":null,
			"pvArrange":null,
			"pvCapacity":"33",
			"pvCapacityUnit":"kWp",
			"pvType":"",
			"quarterReport":null,
			"quarterReportEmail":null,
			"registrationTime":1685694644000,
			"registrationTimeZone":"2023-06-02 16:30:44",
			"series":null,
			"status":2,
			"systemEfficiency":"0",
			"systemType":2,
			"systemTypeName":"Residential solar energy storage (ess)",
			"timezone":94,
			"timezoneName":"(UTC+08:00)BeiJing",
			"timezoneValue":"Asia/Shanghai",
			"todayPowerGeneration":"0",
			"totalCapacity":"0",
			"totalPowerGeneration":"0",
			"upPrice":[
				{
					"endTime":86400,
					"id":751,
					"powerStation":620,
					"price":0.0,
					"startTime":0
				}
			],
			"updateTime":0,
			"updateTimeZone":null,
			"workStatus":null
		}]
}
```

## 32. Charging station update

> Update power station information based on power station ID

> **URL**: /hess/api/chargeSite/update**Method**: POST**Header**: Header： Authorization : token

### Header Description

| Parameter | Type | Description |
| --- | --- | --- |
| Authorization | String | token |

### Request parameters

| Parameter | Type | Length | Description | Mandatory | note |
| --- | --- | --- | --- | --- | --- |
| userToken | String |  | User token | yes |  |
| userType | String | 2 | User Type | no | 0：end-user<br> 1：agent |
| account | String |  | user account | yes |  |
| pwd | String |  | User password encrypted using MD5 | yes |  |
| id | Integer |  | Charging station ID | yes |  |
| adress | String |  | Address of charging station | yes |  |
| countryValue | String |  | Country code | yes | e.g: CN |
| currencyUnitValue | String |  | Currency code | yes | e.g: $ |
| customer | Long |  | Consumer ID of the user | yes |  |
| downPrice | Object |  | Purchase electricity price | yes |  |
| price | Double |  | Purchase electricity price | yes |  |
| startTime | Long |  | time-on | yes | e.g: 0 |
| endTime | Long |  | End Time | yes | e.g: 86400 |
| isShown | Integer |  | Is the charging station visible to the consumer's user | yes | 0: invisible<br> 1: visible |
| latitude | Double |  | latitude | yes |  |
| longitude | Double |  | longitude | yes |  |
| name | String |  | Charging station name | yes |  |
| timezoneValue | String |  | Time zone where the charging station is located | yes | e.g: Asia/Shanghai |

### Response Parameters

| Parameter | Type | Length | Description | Mandatory | Note |
| --- | --- | --- | --- | --- | --- |
| message | String |  | Message code<br> - SUCCESS；<br> - FAIL； |  |  |
| code | String |  | http/ https response code<br> - 200 ok；<br> - 201 Created；<br> - 401 Unauthorized；<br> - 403 Forbidden；<br> - 404 Not Found |  |  |

### Example

```
https://api.livoltek-portal.com:8081/hess/api/chargeSite/update? userToken=xxx&userType=1
https://api-eu.livoltek-portal.com:8081/hess/api/chargeSite/update? userToken=xxx&userType=1
{
  "account": " testAccount",
  "adress": "China NanJing",
  "countryValue": "CN",
  "createSource": 0,
  "currencyUnitValue": "¥",
  "customer": 169710293409792,
  "downPrice": [
    {
      "endTime": 86400,
      "id": 840,
      "powerStation": 702,
      "price": 33,
      "startTime": 0
    }
  ],
  "gridTiedType": 2,
  "id": 702,
  "isShown": 1,
  "latitude": 30,
  "longitude": 120,
 "name": "API test",
  "pwd": "<md5-de-ejemplo-omitido>",
  "timezoneValue": "Asia/Shanghai",
  "upPrice": [
    {
      "endTime": 86400,
      "id": 829,
      "powerStation": 702,
      "price": 22,
      "startTime": 0
    }
  ]
}
```

### Response example

```
{
    "code": "String",
    "message": "String",
}
{
    "code": "200",
    "message": "SUCCESS",
}
```

## 33. Charging station deletion

> Delete a user's charging station based on the charging station ID

> **URL**: /hess/api/chargeSite/disable**Method**: POST**Header**: Header： Authorization : token

### Header Description

| Parameter | Type | Description |
| --- | --- | --- |
| Authorization | String | token |

### Request parameters

| Parameter | Type | Length | Description | Mandatory | note |
| --- | --- | --- | --- | --- | --- |
| userToken | String |  | User token | yes |  |
| userType | String | 2 | User Type | no | 0：end-user<br> 1：agent |
| account | String |  | user account | yes |  |
| pwd | String |  | User password encrypted using MD5 | yes |  |
| id | Integer |  | Charging station ID | yes |  |

### Response Parameters

| Parameter | Type | Length | Description | Mandatory | Note |
| --- | --- | --- | --- | --- | --- |
| message | String |  | Message code<br> - SUCCESS；<br> - FAIL； |  |  |
| code | String |  | http/ https response code<br> - 200 ok；<br> - 201 Created；<br> - 401 Unauthorized；<br> - 403 Forbidden；<br> - 404 Not Found |  |  |

### Example

```
https://api.livoltek-portal.com:8081/hess/api/chargeSite/disable? userToken=xxx&userType=1
https://api-eu.livoltek-portal.com:8081/hess/api/chargeSite/disable? userToken=xxx&userType=1
{
  "account": "admin618",
  "pwd": "<md5-de-ejemplo-omitido>",
  "id":  45502345
}
```

### Response example

```
{
    "code": "String",
    "message": "String",
}
{
    "code": "200",
    "message": "SUCCESS",
}
```

## 34. Charging device creation

> Add charging equipment under the charging station

> **URL**: /hess/api/chargeDevice/create**Method**: POST**Header**: Header： Authorization : token

### Header Description

| Parameter | Type | Description |
| --- | --- | --- |
| Authorization | String | token |

### Request parameters

| Parameter | Type | Length | Description | Mandatory | note |
| --- | --- | --- | --- | --- | --- |
| userToken | String |  | User token | yes |  |
| userType | String | 2 | User Type | no | 0：end-user<br> 1：agent |
| account | String |  | user account | yes |  |
| pwd | String |  | User password encrypted using MD5 | yes |  |
| inverterSn | String |  | Device serial number | yes |  |
| powerStation | Long |  | ID of the power station to which the equipment belongs | yes |  |
| productType | String |  | Product type of equipment | yes |  |

### Response Parameters

| Parameter | Type | Length | Description | Mandatory | Note |
| --- | --- | --- | --- | --- | --- |
| message | String |  | Message code<br> - SUCCESS；<br> - FAIL； |  |  |
| code | String |  | http/ https response code<br> - 200 ok；<br> - 201 Created；<br> - 401 Unauthorized；<br> - 403 Forbidden；<br> - 404 Not Found |  |  |

### Example

```
https://api.livoltek-portal.com:8081/hess/api/chargeDevice/create? userToken=xxx&userType=1
https://api-eu.livoltek-portal.com:8081/hess/api/chargeDevice/create? userToken=xxx&userType=1
{
"account": " admin618",
"pwd": "<md5-de-ejemplo-omitido>",
"inverterSn": "A00012314",
"powerStation": 624,
"productType":"A0070230E11"
}
```

### Response example

```
{
    "code": "String",
    "message": "String",
}
{
    "code": "200",
    "message": "SUCCESS",
}
```

## 35. Charging device query

> Query a charging device

> **URL**: /hess/api/chargeDevice/queryEv**Method**: POST**Header**: Header： Authorization : token

### Header Description

| Parameter | Type | Description |
| --- | --- | --- |
| Authorization | String | token |

### Request parameters

| Parameter | Type | Length | Description | Mandatory | note |
| --- | --- | --- | --- | --- | --- |
| userToken | String |  | User token | yes |  |
| userType | String | 2 | User Type | no | 0：end-user<br> 1：agent |
| account | String |  | user account | yes |  |
| pwd | String |  | User password encrypted using MD5 | yes |  |
| filterSn | String |  | Device serial number | no |  |
| filterStationId | List |  | ID of the power station to which the equipment belongs | no |  |
| filterTime | List |  | Time interval | no |  |
| pageSize | Integer |  | Single page quantity | yes |  |
| start | Integer |  | Number of pages | yes |  |

### Response Parameters

​

| Parameter | Type | Length | Description | Mandatory | Note |
| --- | --- | --- | --- | --- | --- |
| message | String |  | Message code<br> - SUCCESS；<br> - FAIL； |  |  |
| code | String |  | http/ https response code<br> - 200 ok；<br> - 201 Created；<br> - 401 Unauthorized；<br> - 403 Forbidden；<br> - 404 Not Found |  |  |
| batteryType | String |  | Battery type |  |  |
| bmsVersion | String |  | BMS Version |  |  |
| capacity | Integer |  | Capacity |  |  |
| coStatus | Integer |  | Collector status<br> 1- normal,<br> 2- disconnected |  |  |
| countryName | String |  | Country |  |  |
| currencyUnit | String |  | Currency unit |  |  |
| eOut | String |  | Today's electricity generation |  |  |
| gunCount | nteger |  | Number of guns |  |  |
| id | Long |  | device ID |  |  |
| intensity | Integer |  | Signal strength |  |  |
| isDelete | boolean |  | Delete or not<br> 0：normal<br> 1：delete |  |  |
| mcu1Version | String |  | MCU1 Version |  |  |
| mcu2Version | String |  | MCU2 Version |  |  |
| mcu3Version | String |  | MCU3 Version |  |  |
| meterStatus | String |  | Electricity meter status |  |  |
| name | String |  | Device Name |  |  |
| powerStation | Long |  | Station ID |  |  |
| powerStationName | String |  | Name of power station |  |  |
| productType | Long |  | Product model ID |  |  |
| productTypeName | String |  | Product Type |  |  |
| ratedVoltage | String |  | Voltage |  |  |
| registrationTime | String |  | Registration time |  |  |
| registrationTimeZone | String |  | Registration time and time zone conversion |  |  |
| series | Integer |  | Series |  |  |
| status | Integer |  | Device communication status<br> 1- normal,<br> 2- disconnected |  |  |
| systemType | Integer |  | System type |  |  |
| systemTypeName | String |  | System Type Name |  |  |
| template | Long |  | Template |  |  |
| timeZoneName | String |  | Time zone name |  |  |
| timeZoneValue | String |  | Time zone value |  |  |
| upStatus | Integer |  | Upgrade status<br> 1: Upgrading,<br> 2: Upgrade successful,<br> -1: Upgrade failed,<br> 0: ODM abnormal interruption |  |  |
| updateTime | String |  | Update time |  |  |
| workModel | String |  | Working mode <br> 0 Fast charging mode<br> 1 Load balancing<br> 3 Optical storage charging mode |  |  |
| workStatus | Integer |  | running state<br> Working state charging station: <br> upgrading: 5<br> idle: 100; <br> Preparing to start charging: 101; <br> Charging in progress: 102;<br> End of charging: 103;<br> Start failed: 104;<br> Appointment status: 105;<br> System malfunction (unable to charge the car): 106<br> Offline: 3; |  |  |
| workStatusEv | Integer |  | Working status of charging pile gun 1<br> Working status<br> 100 Idle<br> 101 Ready to start charging<br> 102 Charging in progress<br> 103 Charging ended<br> 104 Starting failed<br> 105 Reservation status:<br> Operation stake refers to an appointment within ten minutes;<br> Bluetooth APP is designated for charging<br> 106- System malfunction (unable to charge the car) <br> 5:Upgrading<br> 3: Offline |  |  |

### Example

```
https://api.livoltek-portal.com:8081/hess/api/chargeDevice/queryEv?userToken=xxx&userType=1
https://api-eu.livoltek-portal.com:8081/hess/api/chargeDevice/queryEv?userToken=xxx&userType=1
{
"account": " admin618",
     "pwd": "<md5-de-ejemplo-omitido>",
	"page": 10,
	"size": 1,
	"filterSn": "A00012314",
	"filterStationId": [624],
	"filterTime": ["2023-05-31T16:00:00.000Z", "2023-06-30T15:59:59.000Z"],
}
```

### Response example

```
{
    "code": "String",
    "message": "String",
}
{
 	"code": " String ",
	"message": " String ",
	"data":[
		{
			"batteryType":null,
			"bmsVersion":null,
			"capacity":7,
			"coStatus":1,
			"collectorVersion":null,
			"collector_sn":null,
			"countryName":"China",
			"currencyUnit":"$",
			"eOut":null,
			"groupId":null,
			"groupName":null,
			"gunCount":0,
			"id":280,
			"intensity":null,
			"inverter_sn":"A00012314",
			"is_delete":false,
			"mcu1Version":null,
			"mcu2Version":null,
			"mcu3Version":null,
			"meterStatus":null,
			"name":"A00012314(A0070230E11)",
			"parallelIDType":null,
			"powerStation":624,
			"powerStationName":"szw-test",
			"productTypeName":"A0070230E11",
			"product_type":73,
			"ratedVoltage":"230",
			"registrationTimeZone":"2023-06-10 15:30:16",
			"registration_time":1686382216000,
			"series":7,
			"status":1,
			"systemType":3,
			"systemTypeName":"Residential EV Charger",
			"template":50,
			"timeZoneName":"(UTC+08:00)BeiJing",
			"timeZoneValue":"Asia/Shanghai",
			"updateTime":null,
			"updateTimeZone":null,
			"workModel":null,
			"workStatus":null,
			"workStatusEv":3
		}
	]
}
```

## 36. Charging device delete

> Add charging equipment under the charging station

> **URL**: /hess/api/chargeDevice/disable**Method**: POST**Header**: Header： Authorization : token

### Header Description

| Parameter | Type | Description |
| --- | --- | --- |
| Authorization | String | token |

### Request parameters

| Parameter | Type | Length | Description | Mandatory | note |
| --- | --- | --- | --- | --- | --- |
| userToken | String |  | User token | yes |  |
| userType | String | 2 | User Type | no | 0：end-user<br> 1：agent |
| account | String |  | user account | yes |  |
| pwd | String |  | User password encrypted using MD5 | yes |  |
| id | Integer |  | Device ID | yes |  |

### Response Parameters

| Parameter | Type | Length | Description | Mandatory | Note |
| --- | --- | --- | --- | --- | --- |
| message | String |  | Message code<br> - SUCCESS；<br> - FAIL； |  |  |
| code | String |  | http/ https response code<br> - 200 ok；<br> - 201 Created；<br> - 401 Unauthorized；<br> - 403 Forbidden；<br> - 404 Not Found |  |  |

### Example

```
https://api.livoltek-portal.com:8081/hess/api/chargeDevice/disable? userToken=xxx&userType=1
https://api-eu.livoltek-portal.com:8081/hess/api/chargeDevice/disable? userToken=xxx&userType=1
{
  "account": " admin618",
  "id": 0,
  "pwd": "<md5-de-ejemplo-omitido>"
}
```

### Response example

```
{
    "code": "String",
    "message": "String",
}
{
    "code": "200",
    "message": "SUCCESS",
}
```

## 37. Charging Record Query

> Charging Record Query

> **URL**: /hess/api/chargeRecord**Method**: POST**Header**: Header： Authorization : token

### Header Description

| Parameter | Type | Description |
| --- | --- | --- |
| Authorization | String | token |

### Request parameters

| Parameter | Type | Length | Description | Mandatory | note |
| --- | --- | --- | --- | --- | --- |
| userToken | String |  | User token | yes |  |
| userType | String | 2 | User Type | no | 0：end-user<br> 1：agent |
| account | String |  | user account | yes |  |
| pwd | String |  | User password encrypted using MD5 | yes |  |
| inverterId | String |  | Charger Device ID | no |  |
| siteId | String |  | Power station ID | no |  |
| filterTime | List |  | Time interval | no |  |
| pageSize | Integer |  | Single page quantity | yes |  |
| start | Integer |  | Number of pages | yes |  |

### Response Parameters

​

| Parameter | Type | Length | Description | Mandatory | Note |
| --- | --- | --- | --- | --- | --- |
| message | String |  | Message code<br> - SUCCESS；<br> - FAIL； |  |  |
| code | String |  | http/ https response code<br> - 200 ok；<br> - 201 Created；<br> - 401 Unauthorized；<br> - 403 Forbidden；<br> - 404 Not Found |  |  |
| id | Long |  | Primary key |  |  |
| cards | String |  | Card number |  |  |
| serialNum | String |  | Serial number |  |  |
| clientId | String |  | Device SN number |  |  |
| gunId | Integer |  | Charging gun number |  |  |
| gunType | Integer |  | Charging gun type<br> 0-National standard AC<br> 1-National standard DC<br> 2-European standard AC<br> 3-European standard DC<br> 4-American standard AC<br> 5-American standard DC<br> 6-Japanese standard AC<br> 7-Japanese standard DC |  |  |
| strategy | Integer |  | Charging gun strategy<br> Gun charging strategy<br> 0 automatic charging<br> 1 charging according to time<br> 2 fixed amount<br> 3 charging according to battery level |  |  |
| startTime | Long |  | Charging start time |  |  |
| endTime | Long |  | Charging end time |  |  |
| charging | BigDecimal |  | Charging capacity |  |  |
| amount | BigDecimal |  | Charging amount |  |  |
| initMode | Integer |  | start mode |  |  |
| endReason | Long |  | Reason for stopping |  |  |
| chargTime | Long |  | Charging duration |  |  |
| timeZone | String |  | time zone |  |  |
| solarCharge | Double |  | Energy storage and photovoltaic charging capacity |  |  |
| parameter | Integer |  | Charging strategy parameters<br> Gun charging strategy parameters Time unit is 1 second Amount unit is 0.01 yuan Electricity unit is 0.01kw |  |  |
| maxChargePower | Double |  | Instantaneous maximum charging power |  |  |
| beforCharg | Double |  | Pre charging meter reading |  |  |
| endCharg | Double |  | Meter reading after charging |  |  |
| start | Date |  | Charging start time |  |  |
| end | Date |  | Charging end time |  |  |
| eventNum | Integer |  | Instantaneous value of total charging record entry |  |  |
| inverterId | Long |  | Device ID |  |  |
| gunStart | Long |  | Insertion time |  |  |
| gunEnd | Long |  | Drawing time |  |  |
| gunStatus | Integer |  | Charging gun status<br> 0- Idle<br> 1- Preparing to start charging<br> 2- Charging in progress<br> 3- Charging ended<br> 4- Starting failed<br> 5- Reservation status: Operation stake refers to an appointment within ten minutes; Bluetooth APP is designated for charging<br> 6- System malfunction (unable to charge the car) |  |  |

​

### Example

```
https://api.livoltek-portal.com:8081/hess/api/chargeDevice/chargeRecord? userToken=xxx&userType=1
https://api-eu.livoltek-portal.com:8081/hess/api/chargeDevice/chargeRecord? userToken=xxx&userType=1
{
"account": " admin618",
     "pwd": "<md5-de-ejemplo-omitido>",
	"page": 10,
	"size": 1,
	"inverterId": "12314",
	"siteId":624,
	"filterTime": [1686534638801, 1686534638801]
}
```

### Response example

```
{
    "code": "String",
    "message": "String",
}
{
	"code": " String ",
	"message": " String ",
	"data":[
		{
		"id": 712,
		"cards": "50EF2F23",
		"serialNum": "2306080835229DA67A",
		"clientID": "AC02211H22100327",
		"gunId": 1,
		"gunType": 2,
		"strategy": 0,
		"startTime": 1686184527000,
		"endTime": 1686197075000,
		"charging": 21.800,
		"amount": 15.04,
		"initMode": 0,
		"endReason": 0,
		"chargTime": 12548,
		"timeZone": "Asia/Shanghai",
		"solarCharge": 0.0,
		"parameter": 0,
		"maxChargePower": 6.6,
		"beforCharg": 461.6,
		"endCharg": 2641.8,
		"start": "2023-06-08T00:35:27.000+00:00",
		"end": "2023-06-08T04:04:35.000+00:00",
		"eventNum": 83,
		"inverterId": 256,
		"gunStart": 1686183369000,
		"gunEnd": 1686197075000,
		"stopReasonDetails": []
	}
	]
}
```

## 38. Charging Station Start/Stop

> Charging Station Start/Stop

> **URL**: /hess/api/chargeCommandDown**Method**: POST**Header**: Header： Authorization : token

### Header Description

| Parameter | Type | Description |
| --- | --- | --- |
| Authorization | String | token |

### Request parameters

| Parameter | Type | Length | Description | Mandatory | note |
| --- | --- | --- | --- | --- | --- |
| userToken | String |  | User token | yes |  |
| userType | String | 2 | User Type | no | 0：end-user <br>1：agent |
| account | String |  | user account | yes |  |
| pwd | String |  | User password encrypted using MD5 | yes |  |
| chargeStrategy | Integer |  | Charging strategy<br> -1: Stop charging<br> 0: Until fully charged<br> 1: Charge according to time<br> 2: Charge according to amount<br> 3: Charge according to battery level | yes |  |
| chargeStrategyPar | Integer |  | Charging strategy parameter:<br> When chargeStrategy is 0, fill in 0;<br> When chargeStrategy is 1, transfer the charging duration in seconds, such as 120;<br> When chargeStrategy is 2, transfer the charging amount, such as: 10;<br> When chargeStrategy is 3, transfer the charging charge, such as 100 | yes |  |
| chargeType | Integer |  | Charging effective type 0: Instant charging 2: Appointment charging | yes |  |
| startTime | String |  | Appointment start time, timestamp, in seconds, such as 1693468512 | yes |  |
| sn | String |  | Device SN number | yes |  |

### Response Parameters

​

| Parameter | Type | Length | Description | Mandatory | Note |
| --- | --- | --- | --- | --- | --- |
| message | String |  | Message code<br> - SUCCESS；<br> - FAIL； |  |  |
| code | String |  | http/ https response code<br> - 200 ok；<br> - 201 Created；<br> - 401 Unauthorized；<br> - 403 Forbidden；<br> - 404 Not Found |  |  |

### Example

```
https://api.livoltek-portal.com:8081/hess/api/chargeCommandDown? userToken=xxx&userType=1
https://api-eu.livoltek-portal.com:8081/hess/api/chargeCommandDown? userToken=xxx&userType=1
{
"account": " admin618",
     "pwd": "<md5-de-ejemplo-omitido>",  
    "chargeStrategy": 0,
    "chargeStrategyPar": 0,
    "chargeType": 0,
    "startTime": "string",
    "sn": "string"
}
```

### Response example

```
{
    "code": "String",
    "message": "String",
}
{
    "code": " String ",
    "message": " String ",
}
```

## 39. Charging schedule settings

> Charging schedule settings

> **URL**: /hess/api/chargeSchedule**Method**: POST**Header**: Header： Authorization : token

### Header Description

| Parameter | Type | Description |
| --- | --- | --- |
| Authorization | String | token |

### Request parameters

| Parameter | Type | Length | Description | Mandatory | note |
| --- | --- | --- | --- | --- | --- |
| userToken | String |  | User token | yes |  |
| userType | String | 2 | User Type | no | 0：end-user<br> 1：agent |
| account | String |  | user account | yes |  |
| pwd | String |  | User password encrypted using MD5 | yes |  |
| dayOfWeek | Integer |  | 1: Monday<br> 2:Tuesday<br> 3:Wednesday <br> 4：Thursday <br> 5：Friday <br> 6：Saturday<br> 7：Sunday | yes |  |
| deviceId | String |  | Device ID | yes |  |
| durationHour | Integer |  | Charging duration hours must be greater than -1 and less than 24 | yes |  |
| durationMin | Integer |  | Charging duration minutes, must be 0 or 30 | yes |  |
| startMin | Integer |  | Charging start time minutes, must be 0 or 30 | yes |  |
| startHour | Integer |  | Charging start time hours, must be greater than -1 and less than 24 | yes |  |

### Response Parameters

| Parameter | Type | Length | Description | Mandatory | Note |
| --- | --- | --- | --- | --- | --- |
| message | String |  | Message code<br> - SUCCESS；<br> - FAIL； |  |  |
| code | String |  | http/ https response code<br> - 200 ok；<br> - 201 Created；<br> - 401 Unauthorized；<br> - 403 Forbidden；<br> - 404 Not Found |  |  |

### Example

```
https://api.livoltek-portal.com:8081/hess/api/chargeSchedule? userToken=xxx&userType=1
https://api-eu.livoltek-portal.com:8081/hess/api/chargeSchedule? userToken=xxx&userType=1
{
"account": " admin618",
     "pwd": "<md5-de-ejemplo-omitido>",  
     "dayOfWeek": 0,
     "deviceId": "string",
     "durationHour": 0,
     "durationMin": 0,
     "startMin": 0,
     "startHour": 0
}
```

### Response example

```
{
    "code": "String",
    "message": "String",
}
{
    "code": " String ",
    "message": " String ",
}
```

## 40. Mqtt push device alarm

> Mqtt push device alarm

> **Host-URL**:<br> mqtt://api.livoltek-portal.com:1883 (International servers) mqtt://api-eu.livoltek-portal.com:1883 (European servers)

### Request parameters

| Parameter | Type | Length | Description | Mandatory | note |
| --- | --- | --- | --- | --- | --- |
| username | String |  | user name | yes |  |
| password | String |  | password | yes |  |
| topic | String |  | Mqtt subscription theme | yes | ev_alarm_topic/{sn} e.g: ev_alarm_topic/AC12456 |

### Response Parameters

| Parameter | Type | Length | Description | Mandatory | Note |
| --- | --- | --- | --- | --- | --- |
| deviceId | String |  | Device ID |  |  |
| sn | String |  | Device SN number |  |  |
| alarm | Object |  |  |  |  |
| actionId | String |  | Alarm action |  | 0：alarm，<br>1：fault |
| content | String |  | Alarm code |  |  |
| i18nMap | String |  | Internationalization of alarm content |  |  |
| objId | String |  | Device SN number |  |  |
| originTime | String |  | Alarm occurrence time |  |  |

### Response example

```
{
    "deviceId": 385,  
    "sn": "AC00711H22120025", 
    "alarm": {
    "actionId": "0",  
    "content": "CP-108-21-3 action()",
    "i18nMap": "{\"de\":\"Überspannungsfehler{?}\",\"ru\":\"Отказ от перенапряжения{?}\",\"pt\":\"Falha de sobretensão{?}\",\"ms\":\"Ralat tekanan berlebihan{?}\",\"en\":\"Overvoltage fault{?}\",\"it\":\"Guasto di sovratensione{?}\",\"fr\":\"Défaillance de surtension{?}\",\"zh-CN\":\"过压故障{?}\",\"es\":\"Fallo de sobretensión {?}\",\"ar\":\"أكثر من الجهد خطأ{?}\",\"idn\":\"Kesalahan tekanan berlebihan{?}\",\"vi\":\"Lỗi quá áp{?}\",\"th\":\"ความล้มเหลวของแรงดันไฟฟ้าเกิน{?}\",\"pl\":\"Błąd przepięcia{?}\",\"nl\":\"Overspanningsfout{?}\"}",  
    "objId": "AC00713H22080019", 
    "originTime": 1671092662000   
}
```

## 41. Mqtt push device working status

> The working status of the mqtt push device

> **Host-URL**:<br> mqtt://api.livoltek-portal.com:1883 (International servers) mqtt://api-eu.livoltek-portal.com:1883 (European servers)

### Request parameters

| Parameter | Type | Length | Description | Mandatory | note |
| --- | --- | --- | --- | --- | --- |
| username | String |  | user name | yes |  |
| password | String |  | password | yes |  |
| topic | String |  | Mqtt subscription theme | yes | ev_work_status_topic/{sn} e.g: ev_work_status_topic/AC12456 |

### Response Parameters

| Parameter | Type | Length | Description | Mandatory | Note |
| --- | --- | --- | --- | --- | --- |
| deviceId | String |  | Device ID |  |  |
| sn | String |  | Device SN number |  |  |
| workStatus | String |  | Device working status |  |  |

### Response example

```
{
	"deviceId": 464, 
	"sn": "AC00711H24010301", 
	"workStatus": "Available"  
}
```

## 42. Query the power station ID based on device SN

> Query the power station ID based on device SN

> **Host-URL**:<br> /hess/api[/site/{serialNumber}](https://sandbox.hxgroup.com/hess/api/swagger-ui.html#/operations/common-controller/querySiteIdUsingGET)

### Request parameters

| Parameter | Type | Length | Description | Mandatory | note |
| --- | --- | --- | --- | --- | --- |
| userToken | String |  | User token | yes |  |
| userType | String | 2 | User Type | no | 0：end-user 1：agent |
| serialNumber | String |  | The serial number of the device | yes |  |

### Response Parameters

| Parameter | Type | Length | Description | Mandatory | Note |
| --- | --- | --- | --- | --- | --- |
| powerStationId | String |  | Power station ID |  |  |
| message | String | 265 | Message code - SUCCESS FAIL； |  |  |
| code | String | 13 | http/ https response code<br> - 200 ok；<br> - 201 Created；<br> - 401 Unauthorized；<br> - 403 Forbidden；<br> 404 Not Found |  |  |

### Response example

```
{
	"code": "200",
	"message": "SUCCESS",
	"data": {
		"powerStationId": "955"
	}
}
```

## 43. Site Owner

> Obtain the end users of the power station

> **URL**: /hess/api/site/{siteId}/siteOwner**Method**: GET**Header**: Header: Authorization : token

### Header Description

| Parameter | Type | Description |
| --- | --- | --- |
| Authorization | String | token |

### Request parameters

| Parameter | Type | Length | Description | Mandatory | constraint |
| --- | --- | --- | --- | --- | --- |
| userToken | String |  | User token | yes |  |
| userType | String | 2 | User Type | no | 0- end-user<br>1- agent |
| siteId | Long |  | Unique identifier of the power station | yes |  |

### Response Parameters

| Parameter | Type | Length | Description | Mandatory | constraint |
| --- | --- | --- | --- | --- | --- |
| message | string | 64 | Message code<br>- SUCCESS；<br>- FAIL； |  |  |
| code | String | 10 | http/https response code<br>- 200 ok；<br>- 201 Created；<br>- 401 Unauthorized；<br>- 403 Forbidden；<br>- 404 Not Found |  |  |
| insertTime | Long |  | Creation time |  |  |
| loginAccount | String |  | Login Account |  |  |
| name | String |  | Name |  |  |
| powerStationName | String |  | Name of power station |  |  |
| country | String |  | Country Name |  |  |
| email | String |  | E-mail address |  |  |

### Example

```
   https://api.livoltek-portal.com:8081/hess/api/site/991/customer?userToken=ehnu2NQ&userType=1
   https://api-eu.livoltek-portal.com:8081/hess/api/site/991/customer?userToken=eyhnu2NQ&userType=1
```

### Response example

```
{
  "country": "string",
  "email": "string",
  "insertTime": 0,
  "loginAccount": "string",
  "name": "string",
  "powerStationName": "string"
}
{
    "code": "200",
    "message": "SUCCESS",
    "data": {
        "powerStationName": "FesTest002",
        "name": "fes002",
        "insertTime": 1732513915967,
        "country": "China (Mainland)",
        "email": "fes002@qq.com",
        "loginAccount": "fes002"
    }
}
```

## 44. Device Basic Data

> Obtain basic device data

> **URL**: /hess/api/device/basicData**Method**: GET**Header**: Header: Authorization : token

### Header Description

| Parameter | Type | Description |
| --- | --- | --- |
| Authorization | String | token |

### Request parameters

| Parameter | Type | Length | Description | Mandatory | constraint |
| --- | --- | --- | --- | --- | --- |
| userToken | String |  | User token | yes |  |
| userType | String | 2 | User Type | no | 0- end-user<br>1- agent |
| size | Integer |  | Pagesize of each page:<br>-5<br>-10 (default)<br>-30 | yes |  |
| page | Integer |  | The first site index to be returned in the results, default=1 | yes |  |
| startTime | String |  | Start time for query | no | 2021-03-15 05:47:15 |
| endTime | String |  | End time for query | no | 2024-03-15 05:47:15 |
| Sn | String |  | Device serial number | no |  |

### Response Parameters

| Parameter | Type | Length | Description | Mandatory | constraint |
| --- | --- | --- | --- | --- | --- |
| id | String |  | Device ID |  |  |
| powerStationName | String |  | Power station name |  |  |
| powerStationId | String |  | Power station ID |  |  |
| sn | String |  | Device serial number |  |  |
| longitude | Double |  | Longitude |  |  |
| latitude | Double |  | Latitude |  |  |
| productType | String |  | Device product model |  |  |
| firmwareVersion | String |  | Firmware Version |  |  |
| updateTime | String |  | The last update time of the device |  |  |
| runningStatus | String |  | Running state |  |  |
| communicationStatus | String |  | Device communication status |  |  |
| deviceType | String |  | Device Type |  |  |
| deviceManufacturer | String |  | Device manufacturer |  |  |
| firmwareTypeName | String |  | Firmware Name |  |  |
| powerGenerationDay | String |  | Daily power generation |  |  |
| negativeDay | String |  | Daily grid connected electricity consumption |  |  |
| positiveDay | String |  | Daily purchase of online electricity |  |  |
| chargeDay | String |  | Daily charging capacity |  |  |
| dischargeDay | String |  | Daily discharge capacity |  |  |
| loadDay | String |  | Daily load electricity consumption |  |  |
| timezone | String |  | Time zone where the device is located |  |  |
| registrationTime | String |  | Device registration time |  |  |
| code | String |  | http/ https response code<br>- 200 ok；<br>- 201 Created；<br>- 401 Unauthorized；<br>- 403 Forbidden；<br>404 Not Found |  |  |
| message | String |  | Message code<br>- SUCCESS；<br>- FAIL； |  |  |

### Example

```
   https://api.livoltek-portal.com:8081/hess/api/device/basicData?userType=1&userToken=<token-de-ejemplo-omitido>&sn=GT32501H22520024&startTime=2021-03-15 05:47:15&endTime=2024-03-15 05:47:15
```

### Response example

```
{
    "code": "200",
    "message": "SUCCESS",
    "data": [
        {
            "id": "137",
            "powerStationName": "三相并网机测试电站",
            "powerStationId": "400",
            "sn": "GT32501H22524",
            "longitude": 116.345120,
            "latitude": 39.949070,
            "productType": "GT3-25KD1",
            "firmwareVersion": "DSP1 version:V0.0.0,DSP2 version:V0.0.0,ARM version:V1.2.5,Collector version:null,LCD version:V0.0.0",
            "updateTime": "2025-01-18 15:15:40",
            "runningStatus": "Offline",
            "communicationStatus": "offline",
            "deviceType": "device_inverter",
            "deviceManufacturer": "LIVOLTEK",
            "firmwareTypeName": "DSP1 version,DSP2 version,ARM version,Collector version,LCD version",
            "powerGenerationDay": "12",
            "negativeDay": "50",
            "positiveDay": "50",
            "chargeDay": "51",
            "dischargeDay": "52",
            "loadDay": "15",
            "timezone": "Asia/Shanghai",
            "registrationTime": "2023-03-15 05:47:15"
        }
    ]
}
```

## 45. Device One Day Fault Alarm

> Search device alarm logs in one day by device SN.

> **URL**: /hess/api/device/{siteId}/{serialNumber}/oneDayFaultAlarm**Method**: GET**Header**: Header: Authorization : token

### Header Description

| Parameter | Type | Description |
| --- | --- | --- |
| Authorization | String | token |

### Request parameters

| Parameter | Type | Length | Description | Mandatory | constraint |
| --- | --- | --- | --- | --- | --- |
| userToken | String |  | User token | yes |  |
| userType | String | 2 | User Type | no | 0- end-user<br>1- agent |
| siteId | String |  | Site ID | yes |  |
| serialNumber | Integer |  | Device SN | yes |  |
| size | Integer |  | Pagesize of each page,<br>-5<br>-10 (default)<br>-30 | yes |  |
| page | Integer |  | The first site index to be returned in the results, default=0 | yes |  |
| dateTime | String |  | Datetime for query, which should be in one day | yes | e.g. 2022-01-01 |

### Response Parameters

| Parameter | Type | Length | Description | Mandatory | constraint |
| --- | --- | --- | --- | --- | --- |
| alarmEvent | String | 1024 | Alarm code |  | For internal use |
| alarmStatus | String | 32 | Alarm Status （No）<br>- Active<br>- inactive |  | Under developing |
| alarmCode | String | 256 | Alarm code |  |  |
| alarmName | String | 256 | Alarm description, such as “AC Voltage High” |  |  |
| alarmType | String | 32 | Alarm type:<br>- Notice<br>- fault |  |  |
| originTime | Long | 13 | - Alarm timestamp |  |  |
| deviceType | String | 32 | - Device type |  |  |
| code | String |  | http/https response code<br>- 200 ok；<br>- 201 Created；<br>- 401 Unauthorized；<br>- 403 Forbidden；<br>- 404 Not Found |  |  |
| message | String |  | Message code<br>- SUCCESS；<br>- FAIL； |  |  |
| count | Integer |  |  |  |  |

### Example

```
  https://api.livoltek-portal.com:8081/hess/api/site/123/SN10203/ oneDayFaultAlarm? dateTime=2022-01-01&page=1&size=10&userToken=*****&userType=1
  https://api-eu.livoltek-portal.com:8081/hess/api/site/123/SN10203/ oneDayFaultAlarm? dateTime=2022-01-01&page=1&size=10&userToken=*****&userType=1
```

### Response example

```
{
    "code": " String ",
    "message": " String ",
    "data": {
        "list": [
            {
                "alarmCode": " String ",
                "alarmName": " String ",
                "alarmEvent": " String ",
                "alarmStatus": “String”,
                "alarmType": " String ",
                "originTime": “Long”,
                "deviceType": " String "
            }
        ],
        "count": “Integer”
    }
}

{
    "code": "200",
    "message": "SUCCESS",
    "data": {
        "list": [
            {
                "alarmCode": "Grid voltage high action(0.0 0.0 0.0 0.00 0.00 0.00 208.0 117.8 0.0 0.0 0 0 0)",
                "alarmName": "Grid AC over voltage",
                "alarmEvent": "Grid AC over voltage",
                "alarmStatus": null,
                "alarmType": "0",
                "originTime": 1655757708000,
                "deviceType": "2_19"
            }
        ],
        "count": 1
    }
}
```

## 46. Generate UserToken

> Generate UserToken

> **URL**: /hess/api/user/userToken**Method**: POST**Header**: Header: Authorization : token**Request Rules**: Each terminal with the same name can only call the interface 5 times in 15 minutes, and each terminal user with the same name can only generate 5 valid tokens.

### Header Description

| Parameter | Type | Description |
| --- | --- | --- |
| Authorization | String | token |

### Request parameters

| Parameter | Type | Length | Description | Mandatory | constraint |
| --- | --- | --- | --- | --- | --- |
| userType | String | 2 | User Type | no | 0- end-user<br>1- agent |
| account | String |  | User account | yes |  |
| pwd | String |  | User password encrypted using MD5 | yes |  |
| expiryTime | Long |  | UserToken expiration time | yes |  |

### Response Parameters

| Parameter | Type | Length | Description | Mandatory | constraint |
| --- | --- | --- | --- | --- | --- |
| code | String |  | http/https response code<br>- 200 ok；<br>- 201 Created；<br>- 401 Unauthorized；<br>- 403 Forbidden；<br>- 404 Not Found |  |  |
| message | String |  | Message code<br>- SUCCESS；<br>- FAIL； |  |  |
| data | Object |  | Return data |  |  |

### Example

```
  https://api.livoltek-portal.com:8081/hess/api/user/userToken?userType=1 
  https://api-eu.livoltek-portal.com:8081 /hess/api/user/userToken?userType=1
  
  {
    "account": "test_account",
    "expiryTime": 1739588071000,
    "pwd": "<md5-de-ejemplo-omitido>"
  }
```

### Response example

```
{
    "code": "operate.success",
    "message": null,
    "data": "<token-de-ejemplo-omitido>"
}
```

## 47. UserToken query

> Query the collection of userTokens

> **URL**: /hess/api/user/userTokenList**Method**: POST**Header**: Header: Authorization : token**Request Rules**: Each terminal with the same name can only call the interface 5 times in 15 minutes. Only valid tokens can be queried.

### Header Description

| Parameter | Type | Description |
| --- | --- | --- |
| Authorization | String | token |

### Request parameters

| Parameter | Type | Length | Description | Mandatory | constraint |
| --- | --- | --- | --- | --- | --- |
| userType | String | 2 | User Type | no | 0- end-user<br>1- agent |
| account | String |  | User account | yes |  |
| pwd | String |  | User password encrypted using MD5 | yes |  |

### Response Parameters

| Parameter | Type | Length | Description | Mandatory | constraint |
| --- | --- | --- | --- | --- | --- |
| code | String |  | http/https response code<br>- 200 ok；<br>- 201 Created；<br>- 401 Unauthorized；<br>- 403 Forbidden；<br>- 404 Not Found |  |  |
| message | String |  | Message code<br>- SUCCESS；<br>- FAIL； |  |  |
| data | Object |  | Return data |  |  |
| id | Long |  | ID |  |  |
| insertTime | Long |  | Data insertion time |  |  |
| expiryTime | Long |  | UserToken expiration time |  |  |
| token | String |  | User token |  |  |
| state | String |  | Token status |  |  |
| type | String |  | Data type |  |  |
| ownerNo | String |  | Owner's code |  |  |

### Example

```
  https://api.livoltek-portal.com:8081/hess/api/user/userTokenList?userType=1 
  https://api-eu.livoltek-portal.com:8081 /hess/api/user/userTokenList?userType=1

  
  {
    "account": "test_account",
    "expiryTime": 1739588071000,
    "pwd": "<md5-de-ejemplo-omitido>"
  }
```

### Response example

```
{
    "code": "operate.success",
    "message": null,
    "data": [
        {
            "id": 351417469358083,
            "insertTime": 1739415307323,
            "expiryTime": 1739588071000,
            "token": "<token-de-ejemplo-omitido>",
            "state": "normal",
            "type": "temporary",
            "ownerNo": "customer-0000000000"
        }
    ]
}
```

## 48. Device power report query

> Device power report query

> **URL**: /hess/api/sample/energy**Method**: POST**Header**: Header: Authorization : token**Request Rules**: Each device can only request an interface once per hour The query time interval cannot exceed 24 hours

### Header Description

| Parameter | Type | Description |
| --- | --- | --- |
| Authorization | String | token |

### Request parameters

| Parameter | Type | Length | Description | Mandatory | constraint |
| --- | --- | --- | --- | --- | --- |
| userType | String | 2 | User Type | no | 0- end-user<br>1- agent |
| userToken | String |  | userToken | yes |  |
| id | Long |  | Device ID | yes |  |
| startTime | String |  | Start time | yes |  |
| endTime | String |  | End Time | yes |  |
| interval | Integer |  | Time interval in seconds | no | Default: 3600 (1h)<br>Options: 300 (5min) / 900 (15min) / 1800 (30min) / 3600 (1h) |

### Response Parameters

| Parameter | Type | Length | Description | Mandatory | constraint |
| --- | --- | --- | --- | --- | --- |
| code | String |  | http/https response code<br>- 200 ok；<br>- 201 Created；<br>- 401 Unauthorized；<br>- 403 Forbidden；<br>- 404 Not Found |  |  |
| message | String |  | Message code<br>- SUCCESS；<br>- FAIL； |  |  |
| data | Object |  | Return data |  |  |
| pvYield | List |  | Photovoltaic power generation |  |  |
| loadConsumption | List |  | Load power consumption |  |  |
| epsOutputenergy | List |  | EPS output power |  |  |
| energyImportFromGrid | List |  | Purchasing electricity from the power grid |  |  |
| energyExportToGrid | List |  | The sold electricity transmitted to the power grid |  |  |
| dischargeCapacity | List |  | Battery discharge capacity |  |  |
| chargingCapacity | List |  | Battery charging capacity |  |  |
| dgtotalEnergy | List |  | Diesel power generation |  |  |
| value | Double |  | quantity of electricity |  |  |
| datetime | String |  | Data statistics time |  |  |
| original | Boolen |  | Is it delivered on the device |  |  |

### Example

```
  https://api.livoltek-portal.com:8081/hess/api/sample/energy?userType=1 & userToken=qwrqwrq
  https://api-eu.livoltek-portal.com:8081 /hess/api/user/sample/energy?userType=1 & userToken=qwrqwrq
  
  {
      "startTime": "2025-04-21 00:00:00",
      "endTime": "2025-04-21 23:59:59",
      "id": "1599",
      "interval": 3600
  }
```

### Response example

```
{
  "chargingCapacity": [
    {
      "datetime": "string",
      "original": true,
      "value": 0
    }
  ],
  "dgtotalEnergy": [
    {
      "datetime": "string",
      "original": true,
      "value": 0
    }
  ],
  "dischargeCapacity": [
    {
      "datetime": "string",
      "original": true,
      "value": 0
    }
  ],
  "energyExportToGrid": [
    {
      "datetime": "string",
      "original": true,
      "value": 0
    }
  ],
  "energyImportFromGrid": [
    {
      "datetime": "string",
      "original": true,
      "value": 0
    }
  ],
  "epsOutputenergy": [
    {
      "datetime": "string",
      "original": true,
      "value": 0
    }
  ],
  "loadConsumption": [
    {
      "datetime": "string",
      "original": true,
      "value": 0
    }
  ],
  "pvYield": [
    {
      "datetime": "string",
      "original": true,
      "value": 0
    }
  ]
}
```

## 49. Site day energy query

> Site day energy query

> **URL**: /hess/api/sample/energy/site/day**Method**: POST**Header**: Header: Authorization : token**Request Rules**: Each id can only request an interface once per hour

### Header Description

| Parameter | Type | Description |
| --- | --- | --- |
| Authorization | String | token |

### Request parameters

| Parameter | Type | Length | Description | Mandatory | constraint |
| --- | --- | --- | --- | --- | --- |
| userType | String | 2 | User Type | no | 0- end-user<br>1- agent |
| userToken | String |  | userToken | yes |  |
| id | Long |  | Site ID | yes |  |
| date | String |  | Month date | yes | 2025-07 |

### Response Parameters

| Parameter | Type | Length | Description | Mandatory | constraint |
| --- | --- | --- | --- | --- | --- |
| code | String |  | http/https response code<br>- 200 ok；<br>- 201 Created；<br>- 401 Unauthorized；<br>- 403 Forbidden；<br>- 404 Not Found |  |  |
| message | String |  | Message code<br>- SUCCESS；<br>- FAIL； |  |  |
| data | Object |  | Return data |  |  |
| pvYield | List |  | Photovoltaic power generation |  |  |
| loadConsumption | List |  | Load power consumption |  |  |
| epsOutputenergy | List |  | EPS output power |  |  |
| energyImportFromGrid | List |  | Purchasing electricity from the power grid |  |  |
| energyExportToGrid | List |  | The sold electricity transmitted to the power grid |  |  |
| dischargeCapacity | List |  | Battery discharge capacity |  |  |
| chargingCapacity | List |  | Battery charging capacity |  |  |
| dgtotalEnergy | List |  | Diesel power generation |  |  |
| evConsumption | List |  | Charging pile charging capacity |  |  |
| value | Double |  | quantity of electricity |  |  |
| datetime | String |  | Data statistics time |  |  |

### Example

```
  https://api.livoltek-portal.com:8081/hess/api/sample/energy/site/day?userType=1&userToken=qwrqwrq
  https://api-eu.livoltek-portal.com:8081 /hess/api/user/sample/energy/site/day?userType=1&userToken=qwrqwrq
  
  {
      "date2025-04",
      "id": "1599"
  }
```

### Response example

```
{
  "chargingCapacity": [
    {
      "datetime": "string",
      "value": 0
    }
  ],
  "dgtotalEnergy": [
    {
      "datetime": "string",
      "value": 0
    }
  ],
  "dischargeCapacity": [
    {
      "datetime": "string",
      "value": 0
    }
  ],
  "energyExportToGrid": [
    {
      "datetime": "string",
      "value": 0
    }
  ],
  "energyImportFromGrid": [
    {
      "datetime": "string",
      "value": 0
    }
  ],
  "epsOutputenergy": [
    {
      "datetime": "string",
      "value": 0
    }
  ],
  "loadConsumption": [
    {
      "datetime": "string",
      "value": 0
    }
  ],
  "pvYield": [
    {
      "datetime": "string",
      "value": 0
    }
  ]
 "evConsumption": [
    {
      "datetime": "string",
      "value": 0
    }
  ]

}
```

## 50. Sunspec reboot inverter

> Sunspec reboot inverter

> **URL**: /hess/api/sunspec/command/rebootInverter**Method**: POST**Header**: Header: Authorization : token**Request Rules**: Each id can only request an interface once per hour

### Header Description

| Parameter | Type | Description |
| --- | --- | --- |
| Authorization | String | token |

### Request parameters

| Parameter | Type | Length | Description | Mandatory | constraint |
| --- | --- | --- | --- | --- | --- |
| userType | String | 2 | User Type | no | 0- end-user<br>1- agent |
| userToken | String |  | userToken | yes |  |
| account | String |  | account | yes |  |
| pwd | String |  | password | yes |  |
| sn | String |  | device sn | yes |  |

### Response Parameters

| Parameter | Type | Length | Description | Mandatory | constraint |
| --- | --- | --- | --- | --- | --- |
| code | String |  | http/https response code<br>- 200 ok；<br>- 201 Created；<br>- 401 Unauthorized；<br>- 403 Forbidden；<br>- 404 Not Found |  |  |
| message | String |  | Message code<br>- SUCCESS；<br>- FAIL； |  |  |

### Example

```
  https://api.livoltek-portal.com:8081/hess/api/sunspec/command/rebootInverter?userType=1 & userToken=qwrqwrq
  https://api-eu.livoltek-portal.com:8081/hess/api/sunspec/command/rebootInverter?userType=1 & userToken=qwrqwrq
  {
    "account": "string",
    "pwd": "string",
    "sn": "string"
  }
```

### Response example

```
{
    "code": "String",
    "message": "String",
}

{
    "code": "200",
    "message": "SUCCESS",
}
```

## 51. Sunspec reboot BMS

> Sunspec reboot BMS

> **URL**: /hess/api/sunspec/command/rebootBMS**Method**: POST**Header**: Header: Authorization : token**Request Rules**: Each id can only request an interface once per hour

### Header Description

| Parameter | Type | Description |
| --- | --- | --- |
| Authorization | String | token |

### Request parameters

| Parameter | Type | Length | Description | Mandatory | constraint |
| --- | --- | --- | --- | --- | --- |
| userType | String | 2 | User Type | no | 0- end-user<br>1- agent |
| userToken | String |  | userToken | yes |  |
| account | String |  | account | yes |  |
| pwd | String |  | password | yes |  |
| sn | String |  | device sn | yes |  |

### Response Parameters

| Parameter | Type | Length | Description | Mandatory | constraint |
| --- | --- | --- | --- | --- | --- |
| code | String |  | http/https response code<br>- 200 ok；<br>- 201 Created；<br>- 401 Unauthorized；<br>- 403 Forbidden；<br>- 404 Not Found |  |  |
| message | String |  | Message code<br>- SUCCESS；<br>- FAIL； |  |  |

### Example

```
  https://api.livoltek-portal.com:8081/hess/api/sunspec/command/rebootBMS?userType=1 & userToken=qwrqwrq
  https://api-eu.livoltek-portal.com:8081/hess/api/sunspec/command/rebootBMS?userType=1 & userToken=qwrqwrq
  {
    "account": "string",
    "pwd": "string",
    "sn": "string"
  }
```

### Response example

```
{
    "code": "String",
    "message": "String",
}

{
    "code": "200",
    "message": "SUCCESS",
}
```

## 52. Sunspec some param info

> Sunspec some param info

> **URL**: /hess/api/sunspec/command/info**Method**: POST**Header**: Header: Authorization : token**Request Rules**: Each id can only request an interface once per hour

### Header Description

| Parameter | Type | Description |
| --- | --- | --- |
| Authorization | String | token |

### Request parameters

| Parameter | Type | Length | Description | Mandatory | constraint |
| --- | --- | --- | --- | --- | --- |
| userType | String | 2 | User Type | no | 0- end-user<br>1- agent |
| userToken | String |  | userToken | yes |  |
| account | String |  | account | yes |  |
| pwd | String |  | password | yes |  |
| sn | String |  | device sn | yes |  |

### Response Parameters

| Parameter | Type | Length | Description | Mandatory | constraint |
| --- | --- | --- | --- | --- | --- |
| code | String |  | http/https response code<br>- 200 ok；<br>- 201 Created；<br>- 401 Unauthorized；<br>- 403 Forbidden；<br>- 404 Not Found |  |  |
| message | String |  | Message code<br>- SUCCESS；<br>- FAIL； |  |  |
| data | Object |  | Return data |  |  |
| TOUEnable | Object |  | TOU Enable |  |  |
| Time2BatteryChargePower | Object |  | Time2 Battery Charge Power |  |  |
| pointDesc | String |  | Control point description |  |  |
| pointName | String |  | Control Point Name |  |  |
| uiName | String |  | UI Name of Control Point |  |  |
| address | String |  | address |  |  |
| factor | String |  | factor |  |  |
| template | long |  | template |  |  |
| value | String |  | Value, display on query, issue on setting |  |  |
| pointOrder | String |  | Point Order |  |  |
| pointLen | String |  | Point Length |  |  |
| pointGroupId | String |  | Point Group Id |  |  |
| controlType | long |  | template |  |  |
| functionCode | String |  | Function Code |  |  |

### Example

```
  https://api.livoltek-portal.com:8081/hess/api/sunspec/command/info?userType=1 & userToken=qwrqwrq
  https://api-eu.livoltek-portal.com:8081/hess/api/sunspec/command/info?userType=1 & userToken=qwrqwrq
  {
    "account": "string",
    "pwd": "string",
    "sn": "string"
  }
```

### Response example

```
{
    "code": "200",
    "message": "SUCCESS",
    "data": {
        "TOUEnable": {
            "pointDesc": "TOU 使能", 
            "pointName": "TOU enable", 
            "uiName": "TOUEnable", 
            "address": "45093", 
            "factor": null,
            "template": 60,  
            "value": "85", 
            "pointOrder": "1", 
            "pointLen": "2", 
            "pointGroupId": "1", 
            "controlType": 0, 
            "functionCode": "6" 
        },
        "Time2BatteryChargePower": {
            "pointDesc": "时间段2-电池充放电功率",
            "pointName": "Time 2 Battery charge power",
            "uiName": "Time2BatteryChargePower",
            "address": "45018",
            "factor": "0.01",
            "template": 60,
            "value": "0.00",
            "pointOrder": "1",
            "pointLen": "2",
            "pointGroupId": "1",
            "controlType": 1,
            "functionCode": "6"
        }
},
………
}
```

## 53. Sunspec some param setting

> Sunspec some param setting Sunspec: some param send,need use info interface result , then modify value

> **URL**: /hess/api/sunspec/command/send**Method**: POST**Header**: Header: Authorization : token**Request Rules**: Each id can only request an interface once per hour

### Header Description

| Parameter | Type | Description |
| --- | --- | --- |
| Authorization | String | token |

### Request parameters

| Parameter | Type | Length | Description | Mandatory | constraint |
| --- | --- | --- | --- | --- | --- |
| userType | String | 2 | User Type | no | 0- end-user<br>1- agent |
| userToken | String |  | userToken | yes |  |
| account | String |  | user account | yes |  |
| pwd | String |  | User password encrypted using MD5 | yes |  |
| sn | String |  | Device SN | yes |  |
| points | Array |  | Collection of the following data objects | yes |  |
| pointDesc | String |  | Control point description |  |  |
| pointName | String |  | Control Point Name |  |  |
| uiName | String |  | UI Name of Control Point |  |  |
| address | String |  | address |  |  |
| factor | String |  | factor |  |  |
| template | long |  | template |  |  |
| value | String |  | Value, display on query, issue on setting |  |  |
| pointOrder | String |  | Point Order |  |  |
| pointLen | String |  | Point Length |  |  |
| pointGroupId | String |  | Point Group Id |  |  |
| controlType | long |  | template |  |  |
| functionCode | String |  | Function Code |  |  |

### Response Parameters

| Parameter | Type | Length | Description | Mandatory | constraint |
| --- | --- | --- | --- | --- | --- |
| code | String |  | http/https response code<br>- 200 ok；<br>- 201 Created；<br>- 401 Unauthorized；<br>- 403 Forbidden；<br>- 404 Not Found |  |  |
| message | String |  | Message code<br>- SUCCESS；<br>- FAIL； |  |  |

### Example

```
  https://api.livoltek-portal.com:8081/hess/api/sunspec/command/send?userType=1 & userToken=qwrqwrq
  https://api-eu.livoltek-portal.com:8081/hess/api/sunspec/command/send?userType=1 & userToken=qwrqwrq
  {
    "account": "xxxx",
    "pwd": "xxxx",
    "points": [
      {
        "pointDesc": "最大取电功率",
        "pointName": "Max off-grid power",
        "uiName": "MaxOffGridPower",
        "address": "XXXXX",
        "factor": "0.01",
        "template": 60,
        "value": "123 ",
        "pointOrder": "1",
        "pointLen": "2",
        "pointGroupId": "1",
        "controlType": 1,
        "functionCode": "6"
      }
    ],
    "sn": "xxxx"
  }
```

### Response example

```
{
    "code": "200",
    "message": "SUCCESS"
}
```

## Secciones presentes en el bundle pero fuera del árbol lateral

Existen como módulos de la app y se alcanzan por id, pero no aparecen en el menú de la doc. No se usan por defecto en el adaptador.

### Query station statistics

> Query the number of power stations, installed capacity, current generation and cumulative generation

> **URL**: /hess/api/powerStationStatistics**Method**: GET**Header**: Header: Authorization : token

#### Header Description

| Parameter | Type | Description |
| --- | --- | --- |
| Authorization | String | token |

#### Request parameters

NO

#### Response Parameters

| Parameter | Type | Length | Description | Mandatory | constraint |
| --- | --- | --- | --- | --- | --- |
| siteNum | String |  | Number of power stations |  |  |
| totalCapacity | String |  | Bettery working power |  |  |
| todayGenerate | String |  | Generation today |  |  |
| totalGenerate | String |  | Cumulative power generation |  |  |
| code | Int |  | http/https response code<br>- 200 ok；<br>- 201 Created；<br>- 401 Unauthorized；<br>- 403 Forbidden；<br>- 404 Not Found |  |  |
| message | String |  | Message code<br>- operate.success；<br>- operate.fail； |  |  |

#### Example

```
   https://api.livoltek-portal.com:8081/hess/api/powerStationStatistics
```

#### Response example

```
{
    "code": " String ",
    "message": " String ",
    "data": {
        " siteNum ": " String ",
        " totalCapacity ":"String",
        " todayGenerate ":"String",
        " totalGenerate ":"String"
    }
}
{
    "code": "200",
    "message": "SUCCESS",
    "data": {
        " siteNum": " 50",
        " totalCapacity":"100",
        " todayGenerate":"50.0",
        " totalGenerate":"102.0"
    }
}
```

### Site historical grid import&export in recent 3 days

> Query the power grid electricity in the past three days of the specified power station（Wh）。

> **URL**: /hess/api/site/{siteId}/reissueUtilityEnergy**Method**: GET**Header**: Header: Authorization : token

#### Header Description

| Parameter | Type | Description |
| --- | --- | --- |
| Authorization | String | token |

#### Request parameters

| Parameter | Type | Length | Description | Mandatory | constraint |
| --- | --- | --- | --- | --- | --- |
| userToken | String |  | User token | yes |  |
| userType | String | 2 | User Type | no | 0- end-user<br>1- agent |
| siteId | String |  | Site ID | yes |  |

#### Response Parameters

| Parameter | Type | Length | Description | Mandatory | constraint |
| --- | --- | --- | --- | --- | --- |
| positive | String |  | Power purchase |  |  |
| negative | String |  | Grid connected electricity |  |  |
| ts | String |  | Time stamp |  | Example：1665100800000 |
| siteId | String |  | Site ID |  |  |
| message | String | 265 | Message code<br>- SUCCESS <br>- FAIL； |  |  |
| code | String | 13 | http/https response code<br>- 200 ok；<br>- 201 Created；<br>- 401 Unauthorized；<br>- 403 Forbidden；<br>- 404 Not Found |  |  |

#### Example

```
    https://api.livoltek-portal.com:8081/hess/api/site/123/ reissueUtilityEnergy? userToken =1& siteId =1123& userType =1
```

#### Response example

```
{
    "data": [ {
        " positive ": " string ",
        " negetive ": " string ",
        " ts ": " string ",
        "siteId": " string "
    }], 
    "message": "string",
    " code ": "string"
}
{
    "code": "200",
    "message": "SUCCESS",
    "data": [
        {
            "siteId": "562",
            "ts": "1665100800000",
            "positive": "131.972",
            "negative": "131.972"
        },
        {
            "siteId": "562",
            "ts": "1665187200000",
            "positive": "131.972",
            "negative": "131.972"
        },
        {
            "siteId": "562",
            "ts": "1665273600000",
            "positive": "131.972",
            "negative": "131.972"
        }
    ]
}
```

### Site historical solar generation in recent 3 days

> Query the historical photovoltaic power generation of the specified power station in the past three days（Wh）。

> **URL**: /hess/api/site/{siteId}/reissueSolarEnergy**Method**: GET**Header**: Header: Authorization : token

#### Header Description

| Parameter | Type | Description |
| --- | --- | --- |
| Authorization | String | token |

#### Request parameters

| Parameter | Type | Length | Description | Mandatory | constraint |
| --- | --- | --- | --- | --- | --- |
| userToken | String |  | User token | yes |  |
| userType | String | 2 | User Type | no | 0- end-user<br>1- agent |
| siteId | String |  | Site ID | yes |  |

#### Response Parameters

| Parameter | Type | Length | Description | Mandatory | constraint |
| --- | --- | --- | --- | --- | --- |
| powerGeneration | String | 10 | PV power generation |  |  |
| ts | String |  | Time stamp |  | Example：1665100800000 |
| siteId | String |  | Site ID |  |  |
| message | String | 265 | Message code<br>- SUCCESS <br>- FAIL； |  |  |
| code | String | 13 | http/https response code<br>- 200 ok；<br>- 201 Created；<br>- 401 Unauthorized；<br>- 403 Forbidden；<br>- 404 Not Found |  |  |

#### Example

```
   https://api.livoltek-portal.com:8081/hess/api/site/123/reissueSolarEnergy? userToken =1& siteId =1123& userType =1
```

#### Response example

```
{
    "code": " String ",
    "message": " String ",
    "data": {
        [{
            "siteId": "siteId",
            "powerGeneration":"String",
            "ts":"String"
        }]
    }
}
{
    "code": "200",
    "message": "SUCCESS",
    "data": [
    {
        "siteId": "562",
        "ts": "1665100800000",
        "powerGeneration": "65.986"
    },
    {
        "siteId": "562",
        "ts": "1665187200000",
        "powerGeneration": "131.972"
    },
    {
        "siteId": "562",
        "ts": "1665273600000",
        "powerGeneration": "131.972"
    }]
}
```
