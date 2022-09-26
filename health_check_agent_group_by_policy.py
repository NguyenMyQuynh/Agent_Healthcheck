# -*- coding: utf-8 -*-

#Ver 1.2

import config
import urllib3
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

import telegram
import json
import requests
import threading

from datetime import datetime
from thehive4py.api import TheHiveApi 
from thehive4py.models import Alert

def rename(old_dict,old_name,new_name):
    new_dict = {}
    for key,value in zip(old_dict.keys(),old_dict.values()):
        new_key = key if key != old_name else new_name
        new_dict[new_key] = old_dict[key]
    return new_dict

# Get agent's status
def AgentStatus(FLEET_URL, FLEET_PORT, FLEET_USERNAME, FLEET_PASSWORD):    
    auth = (FLEET_USERNAME, FLEET_PASSWORD)

    if FLEET_URL == "hsoc.vn/monitor":
        request = requests.get(f"https://{FLEET_URL}/api/fleet/agent_status", auth=auth, verify=False)
    else:
        request = requests.get(f"https://{FLEET_URL}:{FLEET_PORT}/api/fleet/agent_status", auth=auth, verify=False)
    result = json.loads(request.text)

    online = result['results']['online']
    offline = result['results']['offline']

    return (online, offline)

# Get offline agent's info
def OfflineAgentInfo(FLEET_URL, FLEET_PORT, FLEET_USERNAME, FLEET_PASSWORD):
    auth = (FLEET_USERNAME, FLEET_PASSWORD)

    if FLEET_URL == "hsoc.vn/monitor":
        request = requests.get(f"https://{FLEET_URL}/api/fleet/agents", auth=auth, verify=False)
    else:
        request = requests.get(f"https://{FLEET_URL}:{FLEET_PORT}/api/fleet/agents", auth=auth, verify=False)
    result = json.loads(request.text)

    offline_agents = []
    agents_offline_by_policy = {}
    number_offline = 0

    for agent in result['list']:
        status = agent['status']
        # if status == 'offline':
        if status != 'healthy' and status != 'online':
            hostname = agent['local_metadata']['host']['hostname']
            ip = agent['local_metadata']['host']['ip']
            os = agent['local_metadata']['os']['full']
            status = status
            last_checkin = agent['last_checkin']
            offline_agents.append((hostname, ip, os, status, last_checkin))
            policy_id = agent["policy_id"]

            if policy_id not in agents_offline_by_policy:
                agents_offline_by_policy[policy_id] = []

            agents_offline_by_policy[policy_id].append((hostname, ip, os, status, last_checkin))
            
            try:
                last_checkin = agent['last_checkin']
            except:
                last_checkin = "NoCheckin"

            number_offline += 1
            if (number_offline >= 3):
                break


    if FLEET_URL == "hsoc.vn/monitor":
        request = requests.get(f"https://{FLEET_URL}/api/fleet/agent_policies", auth=auth, verify=False)
    else:
        request = requests.get(f"https://{FLEET_URL}:{FLEET_PORT}/api/fleet/agent_policies", auth=auth, verify=False)
    result = json.loads(request.text)

    for id in agents_offline_by_policy.keys():
        for item in result["items"]:
            if id == item["id"]:
                agents_offline_by_policy = rename(agents_offline_by_policy, id, item["name"])
    print(agents_offline_by_policy)
    
    return agents_offline_by_policy

def SendAlertToTheHive(THEHIVE_SERVER, THEHIVE_PORT, THEHIVE_TOKEN, alert):
    alert = alert.replace("\n", "\n\n")

    api = TheHiveApi(f"http://{THEHIVE_SERVER}:{THEHIVE_PORT}", THEHIVE_TOKEN) 
    alert = Alert(
        title='Anomal hostname', 
        description=alert, 
        type='external', 
        source=f'instance-{str(datetime.now())}', 
        sourceRef='alert-ref',
    ) 
   
    api.create_alert(alert) 

def SendAlertToTelegram(TELEGRAM_TOKEN, TELEGRAM_ID, alert):
    telegram_alert = telegram.Bot(TELEGRAM_TOKEN)
    telegram_alert.send_message(chat_id=TELEGRAM_ID, text=alert)

def main():
    alert = "\t=== SOC Agent Health Check ===\n"
    for i in config.FLEET_SERVERS:
        online, offline = AgentStatus(config.FLEET_SERVERS[i]["FLEET_URL"], config.FLEET_SERVERS[i]["FLEET_PORT"], config.FLEET_SERVERS[i]["FLEET_USERNAME"], config.FLEET_SERVERS[i]["FLEET_PASSWORD"])
        alert += f">>>>> {config.FLEET_SERVERS[i]['FLEET_URL']} <<<<<\n"

        if offline == 0:
            alert += f"Online: {online},\t Offline: {offline} ✅\n"
        else:
            alert += f"Online: {online},\t Offline: {offline} ❌.\t"
            alert += "List Offline:\n"

        print(f"FLEET_SERVER: {config.FLEET_SERVERS[i]['FLEET_URL']}")
        print("Online: ", online)
        print("Offline: ", offline)

        agents_offline_by_policy = OfflineAgentInfo(config.FLEET_SERVERS[i]["FLEET_URL"], config.FLEET_SERVERS[i]["FLEET_PORT"], config.FLEET_SERVERS[i]["FLEET_USERNAME"], config.FLEET_SERVERS[i]["FLEET_PASSWORD"])

        for i, policy in enumerate(agents_offline_by_policy):
            alert += f"Policy{i+1}: \t{policy}\n"

            for i, agent in enumerate(agents_offline_by_policy[policy]):
                hostname, ips, os, status, last_checkin = agent
                ip_list = []
                for ip in ips:
                    if ip[0:2] == "10" or ip[0:6] == "172.16" or ip[0:7] == "192.168":
                        ip_list.append(ip)
                
                alert += f"{i + 1}.\t"
                alert += f"Hostname: {hostname},\t"
                alert += f"IP: {ip_list},\t"
                alert += f"OS: {os},\t"
                alert += f"Status: {status},\t"
                alert += f"LastSeen: {last_checkin}\n"
            alert += "_______________________________\n"

    SendAlertToTelegram(config.TELEGRAM_TOKEN, config.TELEGRAM_ID, alert)
    SendAlertToTheHive(config.THEHIVE_SERVER, config.THEHIVE_PORT, config.THEHIVE_TOKEN, alert)

main()
Footer
