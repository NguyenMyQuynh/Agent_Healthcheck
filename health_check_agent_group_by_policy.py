# -*- coding: utf-8 -*-

#Ver 1.2
import config
import urllib3
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
import shlex
import subprocess
import json
import requests
import telegram 

from datetime import datetime
from thehive4py.api import TheHiveApi 
from thehive4py.models import Alert

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
        request = requests.get(f"https://{FLEET_URL}/api/fleet/agents?page=1&perPage=5000", auth=auth, verify=False)
    else:
        request = requests.get(f"https://{FLEET_URL}:{FLEET_PORT}/api/fleet/agents?page=1&perPage=5000", auth=auth, verify=False)
    result = json.loads(request.text)

    # number_offline=0
    offline_agents = []
    for agent in result['list']:
        status = agent['status']
        if status != 'healthy' and status != 'online':
            # number_offline +=1
            hostname = agent['local_metadata']['host']['hostname']
            ip = agent['local_metadata']['host']['ip']
            os = agent['local_metadata']['os']['full']
            policy_id = agent['policy_id']   
            status = status
            try:
                last_checkin = agent['last_checkin']
            except:
                last_checkin = "NoCheckin"
            offline_agents.append((hostname, ip, os, status, last_checkin, policy_id )) 
            # if (number_offline >= 3):
            #     break

    return offline_agents

# Get offline agent's info
def OnlineAgentInfo(FLEET_URL, FLEET_PORT, FLEET_USERNAME, FLEET_PASSWORD):
    auth = (FLEET_USERNAME, FLEET_PASSWORD)

    if FLEET_URL == "hsoc.vn/monitor":
        request = requests.get(f"https://{FLEET_URL}/api/fleet/agents?page=1&perPage=5000", auth=auth, verify=False)
    else:
        request = requests.get(f"https://{FLEET_URL}:{FLEET_PORT}/api/fleet/agents?page=1&perPage=5000", auth=auth, verify=False)
    result = json.loads(request.text)
  
    # number_online=0
    online_agents = []
    for agent in result['list']:
        status = agent['status']
        if status == 'online':
            # number_online +=1
            hostname = agent['local_metadata']['host']['hostname']
            ip = agent['local_metadata']['host']['ip']
            os = agent['local_metadata']['os']['full']
            policy_id = agent['policy_id']   
            status = status
            try:
                last_checkin = agent['last_checkin']
            except:
                last_checkin = "NoCheckin"
            online_agents.append((hostname, ip, os, status, last_checkin, policy_id )) 
            # if (number_online >= 3):
            #     break

    return online_agents

def SendAlertToTheHive(THEHIVE_SERVER, THEHIVE_PORT, THEHIVE_TOKEN, alert):
    alert = alert.replace("\n", "\n\n\n ")
    alert = alert.replace(">>>> ", "\>>>>")

    api = TheHiveApi(f"http://{THEHIVE_SERVER}:{THEHIVE_PORT}", THEHIVE_TOKEN) 
    alert = Alert(
        title='Anomal Loss Dataset', 
        description=alert, 
        type='external', 
        source=f'instance-{str(datetime.now())}', 
        sourceRef='alert-ref',
    ) 
   
    api.create_alert(alert)

def SendAlertToTelegram(TELEGRAM_TOKEN, TELEGRAM_ID, alert):
    telegram_alert = telegram.Bot(TELEGRAM_TOKEN)
    telegram_alert.send_message(chat_id=TELEGRAM_ID, text=alert)

def change(FLEET_URL, FLEET_PORT, FLEET_USERNAME, FLEET_PASSWORD, id):
    auth = (FLEET_USERNAME, FLEET_PASSWORD)

    if FLEET_URL == "hsoc.vn/monitor":
        request = requests.get(f"https://{FLEET_URL}/api/fleet/agent_policies", auth=auth, verify=False)
    else:
        request = requests.get(f"https://{FLEET_URL}:{FLEET_PORT}/api/fleet/agent_policies", auth=auth, verify=False)
    result = json.loads(request.text)
    
    for item in result["items"]:
        if item["id"]==id:
            return item["name"]

def GetAgentOnlineSeperateByPolicy(online_agents):
    listAgentOnlineSeperateByPolicy={}
    for i, agent in enumerate(online_agents):
        hostname, ips, os, status, last_checkin, policy_id = agent
        ip_list = []
        for ip in ips:
            if ip[0:2] == "10" or ip[0:6] == "172.16" or ip[0:7] == "192.168":
                ip_list.append(ip)
                break
        info_agent = ([hostname, status, last_checkin, policy_id])
        if policy_id not in listAgentOnlineSeperateByPolicy:
            listAgentOnlineSeperateByPolicy[policy_id] = []
        if info_agent not in listAgentOnlineSeperateByPolicy[policy_id]:
            listAgentOnlineSeperateByPolicy[policy_id].append(info_agent)        
    return listAgentOnlineSeperateByPolicy       
        
def GetAgentOfflineSeperateByPolicy(offline_agents):
    listAgentOfflineSeperateByPolicy={}
    number_offline=0
    for i, agent in enumerate(offline_agents):
        hostname, ips, os, status, last_checkin, policy_id = agent
        ip_list = []
        for ip in ips:
            if ip[0:2] == "10" or ip[0:6] == "172.16" or ip[0:7] == "192.168":
                ip_list.append(ip)
                break
        info_agent = ([hostname, status, last_checkin, policy_id])
        if policy_id not in listAgentOfflineSeperateByPolicy:
            listAgentOfflineSeperateByPolicy[policy_id] = []
        if info_agent not in listAgentOfflineSeperateByPolicy[policy_id]:
            listAgentOfflineSeperateByPolicy[policy_id].append(info_agent)
    return listAgentOfflineSeperateByPolicy

def main():
    alert = "\t=== SOC Agent Health Check ===\n"
    for i in config.FLEET_SERVERS:
        online, offline = AgentStatus(config.FLEET_SERVERS[i]["FLEET_URL"], config.FLEET_SERVERS[i]["FLEET_PORT"], config.FLEET_SERVERS[i]["FLEET_USERNAME"], config.FLEET_SERVERS[i]["FLEET_PASSWORD"])
        
        alert += f">>>> {config.FLEET_SERVERS[i]['FLEET_URL']} <<<<\n"
        if offline == 0:
            alert += f"Agents online: {online},\t agent offline: {offline}✅\n"
        else:
            alert += f"Online: {online}\t Offline: {offline}. List Offline : \n"

        print("Number of online agents: ", online)
        print("Number of offline agents: ", offline)

        offline_agents = OfflineAgentInfo(config.FLEET_SERVERS[i]["FLEET_URL"], config.FLEET_SERVERS[i]["FLEET_PORT"], config.FLEET_SERVERS[i]["FLEET_USERNAME"], config.FLEET_SERVERS[i]["FLEET_PASSWORD"])
        online_agents = OnlineAgentInfo(config.FLEET_SERVERS[i]["FLEET_URL"], config.FLEET_SERVERS[i]["FLEET_PORT"], config.FLEET_SERVERS[i]["FLEET_USERNAME"], config.FLEET_SERVERS[i]["FLEET_PASSWORD"])

        listAgentOfflineSeperateByPolicy = GetAgentOnlineSeperateByPolicy(offline_agents)
        listAgentOnlineSeperateByPolicy = GetAgentOnlineSeperateByPolicy(online_agents)
        alert += "_______________________________\n"

        tmp = 0
        for i, policy in enumerate(listAgentOfflineSeperateByPolicy):
                    id = policy
                    id = change(config.FLEET_SERVERS[1]["FLEET_URL"], config.FLEET_SERVERS[1]["FLEET_PORT"], config.FLEET_SERVERS[1]["FLEET_USERNAME"], config.FLEET_SERVERS[1]["FLEET_PASSWORD"], id)
                    alert += f"\n Policy{i+1}: {id} \n"
                    if policy not in listAgentOnlineSeperateByPolicy:
                        alert += f"Onine: 0   "
                    else:
                        alert += f"Online: {len(listAgentOnlineSeperateByPolicy[policy])} \t"
                    alert += f"Offline: { len(listAgentOfflineSeperateByPolicy[policy])} ❌ \n"
                    alert += f"List ofline:\n"
                    count=0
                    for info_agent in listAgentOfflineSeperateByPolicy[policy]:
                        tmp=0
                        alert += f"[{count+1}]. "
                        for detail_info in info_agent:
                            if (tmp == 1 or tmp == 0):  
                                alert += f"{detail_info}, \t"
                            if tmp == 2:
                                alert += f"LastSeen: {detail_info}\n"                  
                            tmp = tmp + 1
                        count = count + 1
                        if (count >= 3):
                            break
                    tmp = i+1
        
        for i, policy in enumerate(listAgentOnlineSeperateByPolicy):
            if policy not in listAgentOfflineSeperateByPolicy:
                id = policy
                id = change(config.FLEET_SERVERS[1]["FLEET_URL"], config.FLEET_SERVERS[1]["FLEET_PORT"], config.FLEET_SERVERS[1]["FLEET_USERNAME"], config.FLEET_SERVERS[1]["FLEET_PASSWORD"], id)
                alert += f"\n Policy{tmp+1}: {id} ✅ \n"
                tmp+=1
                alert += f"Online: {len(listAgentOnlineSeperateByPolicy[policy])}   "
                alert += f"Offline: 0 \n"
                

    print(f"\n{alert}")
    
    SendAlertToTheHive(config.THEHIVE_SERVER, config.THEHIVE_PORT, config.THEHIVE_TOKEN, alert)
    SendAlertToTelegram(config.TELEGRAM_TOKEN, config.TELEGRAM_ID, alert)

main()
