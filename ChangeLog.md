# Change Log

## 0.5.5 2025-02-18
- initiate github pages
- initiate file-folder from export-device-configs

## 0.5.4 20205-12-28
- implement test-configlet

## 0.5.3 20204-12-27
- implement import-dci in yaml/json

## 0.5.2 20204-12-20
- modularize cli
- implement export-dci in yaml output

## 0.5.0 2024-12-18
- change to uv from poetry

## 0.4.27 2024-09-13
- implement export-iplink

## 0.4.25 2024-08-21
- implement deploy_mode in import_generic_system

## 0.4.23 2024-08-07
- fix logfile error in Windows
- fix generic system import failing on brand new switch

## 0.4.22 2024-08-07
- implement file logging with ck_apstra_api_<timestame>

## 0.4.21 2024-08-07
- implement import-iplink-ct

## 0.4.20 2024-08-02
- show error for rename interface

## 0.4.19 2024-08-01
- strip ifname in generic_system

## 0.4.18 2024-07-31
- ignore ct name 'na'

## 0.4.17 2024-07-31
- use __init__.py to simplify import 
- generic_system add_vlan remove first to avoid duplicate

## 0.4.16 2024-07-30
- add error log for generic_system add_vlan 

## 0.4.15 2024-07-26
- enhance error handling for missing CT
 
## 0.4.14 2024-07-19
- implement import-virtual-network and export-virtual-network (phase 1)

## 0.4.13 2024-07-18
- implement import-blueprint

## 0.4.12 2024-07-17
- implement export-device-configs

## 0.4.11 2024-07-17
- implement export-blueprint

## 0.4.10 2024-07-09
- implement export-systems

## 0.4.9 2024-07-09
- import-generic-system sync system tags and links tags

## 0.4.8 2024-07-09
- get_temp_vn now retrieve all the vlan_id within bound_to in addition to reserved_vlan_id

## 0.4.7 2024-07-08
- revise relocate-vn with get_temp_vn

## 0.4.3 2024-07-01
- fix prep_logging to return logger

## 0.4.2 2024-06-29
- adjust the logging color of cli

## 0.4.1 2024-06-29
- rename cli: generic-system to import-generic-system
- add cli: export generic system - WIP
- implement cli: version option

