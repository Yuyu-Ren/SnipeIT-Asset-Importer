#!/usr/bin/env python3
import requests
import csv
import glob
import json
import re
import time


def send_request(access_token, request):
    s = requests.session()
    request.headers.update({
            'Authorization': 'Bearer '+access_token,
            'Accept': 'application/json',
            'Content-Type': 'application/json'
            })
    prepped = request.prepare()
    result = s.send(prepped)
    if result.status_code == 405:
        print("Sleeping for 20 seconds...")  # TODO: Implement exponential backoff
        time.sleep(20)
        send_request(accessToken, request)
    else:
        return result


def get_model_id(asset_number):
    assets = ["", "", "", 'OptiPlex 9020', 'OptiPlex 990']
    for i in range(0, len(assets)):
        if asset_number in assets[i]:
            return i+1
    return 6  # Returns mismatched model on no match


def get_status_id(status):
    status_ids = ['Pending', 'Ready to Deploy', 'Archived', 'Errored']
    for i in range(0, len(status_ids)):
        if status in status_ids[i]:
            return i+1
    return 4  # Returns Errored state on no match


def get_csv_data():
    formatted_rows = []
    for file in glob.glob('*.csv'):
        with open(file, newline='') as csvfile:
            reader = csv.reader(csvfile, delimiter=',', quotechar='"')
            for row in reader:
                name = row[0] if row[0] else file+"error"
                asset_tag = row[1] if row[1] else file+"error"
                status_id = get_status_id(row[5]) if row[5] else file+"error"
                model_id = get_model_id(row[2]) if row[2] else file+"error"
                serial = row[4] if row[4] else file+"error"
                chassis = row[7] if row[7] else file+"error"
                operating_system = row[8] if row[8] else file+"error"
                OS_install_date = row[9] if row[9] else file+"error"
                RAM = row[12] if row[12] else file+"error"
                HDD_size = row[15] if row[15] else file+"error"
                IP = row[17] if row[17] else file+"error"
                MAC = row[19] if row[19] else file+"error"
                formatted_rows.append({
                    'name': name,
                    'asset_tag': asset_tag,
                    'status_id': status_id,
                    'model_id': model_id,
                    'serial': serial,
                    'chassis': chassis,
                    'operating_system': operating_system,
                    'OS_install_date': OS_install_date,
                    'RAM': RAM,
                    'HDD_size': HDD_size,
                    'IP': IP,
                    'MAC': MAC
                })
    return formatted_rows


def bulk_import_assets(accessToken: str):
    computers = get_csv_data()
    for computer in computers:
        print(computer)
        result = send_request(accessToken, __import_asset(computer))
        if result is None:
            print("Error: " + str(computer))
            continue
        if result.status_code == 200:
            json_dump = result.json()
            if 'asset_tag' in json_dump['messages']:
                send_request(accessToken, __update_asset(computer, __get_asset_id(accessToken, computer)))




def __get_asset_id(accessToken : str, computer):
    url = 'http://snipeit/api/v1/hardware'
    raw_response = send_request(accessToken, requests.Request(method='GET', url=url))
    if raw_response is None:
        return None
    response = raw_response.json()
    for i in response['rows']:
        if computer['asset_tag'] in i['asset_tag']:
            return i['id']
    return None


def __update_asset(computer: dict, asset_id):
    url = 'http://snipeit/api/v1/hardware/{}'.format(asset_id)
    payload = {
            'status_id': computer['status_id'],
            'model_id': computer['model_id'],
            'asset_tag': computer['asset_tag'],
            'name': computer['name'],
            'serial': computer['serial'],
            '_snipeit_chassis_2': computer['chassis'],
            '_snipeit_operating_system_3': computer['operating_system'],
            '_snipeit_operating_system_installation_date_4': computer['OS_install_date'],
            '_snipeit_physical_ram_installed_5': computer['RAM'],
            '_snipeit_total_disk_space_6': computer['HDD_size'],
            '_snipeit_ip_address_7': computer['IP'],
            '_snipeit_mac_address_ethernet_8': computer['MAC']
         }
    return requests.Request(method='put', url=url, data=json.dumps(payload))
   

def __import_asset(computer: dict):
    url = 'http://snipeit/api/v1/hardware'
    payload = {
            'status_id': computer['status_id'],
            'model_id': computer['model_id'],
            'asset_tag': computer['asset_tag'],
            'name': computer['name'],
            'serial': computer['serial'],
            '_snipeit_chassis_2': computer['chassis'],
            '_snipeit_operating_system_3': computer['operating_system'],
            '_snipeit_operating_system_installation_date_4': computer['OS_install_date'],
            '_snipeit_physical_ram_installed_5': computer['RAM'],
            '_snipeit_total_disk_space_6': computer['HDD_size'],
            '_snipeit_ip_address_7': computer['IP'],
            '_snipeit_mac_address_ethernet_8': computer['MAC']
        }
    return requests.Request(method='POST', url=url, data=json.dumps(payload))


# Fake Access Token while I figure out the API design
accessToken='''eyJ0eXAiOiJKV1QiLCJhbGciOiJSUzI1NiIsImp0aSI6IjVhZjk3NTE5OWRkYWE2YWViZTJlN2I3ODU2MzhjYzlhOWQzZWEzM2E3YWJiZTE1YTJkYjAwOTdlMmM5ZmVhODU4ZGY4ZjQyNzA2YjFiNDNkIn0.eyJhdWQiOiIxIiwianRpIjoiNWFmOTc1MTk5ZGRhYTZhZWJlMmU3Yjc4NTYzOGNjOWE5ZDNlYTMzYTdhYmJlMTVhMmRiMDA5N2UyYzlmZWE4NThkZjhmNDI3MDZiMWI0M2QiLCJpYXQiOjE1NzczMTExNjYsIm5iZiI6MTU3NzMxMTE2NiwiZXhwIjoxNjA4OTMzNTY2LCJzdWIiOiIxIiwic2NvcGVzIjpbXX0.IkhRo2ke3GYsWBwII5HdtUMutpYeV7P1COj_v7-cSKz-jRPKlZv4VG2O9WdyHa1pR6yUq1N2Y9dIyliDA_6EpSPJOo95kVJqpv1oKDBaXDxIxHMeu0IZn-e-5Nl-rsV8UdzkrgqtBI8A-_5WOMar_Crp9RFLHDuMhhSvfJSOdKBOqxBxdWWpRtwuQtvfa-S0zhcSdXqoGoyRBpKD1jbvoHAF7nbFj98si-L0axv2agSVLO93ftl6LRMKD6hNjon_dA1Bl55hNEZpcHQFd6McFLkQudoOh3w0ZDpqgQt8TXH036_uUGP9pXViAQtxzrnT-U1qxxh-ljntrw3undQUjI0BpNwFg2H_rZu1d6K-zt9aSYQ4CpBE4nEvMjqTGhQTBfFoS3orXZKy2ElRngypLpfUHhIjfkHp_VfobK_Ur49De5cQXm0vHZJDV6GQ0_qIsKqYV0xqZoWe1NnMKMPbxM2FjYAU4Hqnlt7Xwqah7MKH8SppQ563L90OyL4UO-ZlveQ14kNEY4QmeeOUrOBIP-JwlEk8mkss_AqQo4wB9KP_m0G2Rp2XEec2YRoSJ8WNqRw16119sttG2caDcd45SASplHNgxZyLhfdMBL4auc03E6aY-Au6Kd9gsSUFpHCv826tc_FLiNgRuvEEhp6bsruMnU6gNNl4ae6PfJBsPCo'''
bulk_import_assets(accessToken)
