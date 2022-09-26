import config

import shlex
import subprocess
import json
import urllib

from datetime import datetime

# Get agent's status
def AgentStatus(FLEET_URL, FLEET_PORT, FLEET_USERNAME, FLEET_PASSWORD):    
    cmd = f'curl --insecure -X GET "https://{FLEET_URL}:{FLEET_PORT}/api/fleet/agent_status" -u "{FLEET_USERNAME}:{FLEET_PASSWORD}"'
    args = shlex.split(cmd)
    process = subprocess.Popen(args, shell=False, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    stdout, stderr = process.communicate()

    result = json.loads(stdout.decode('utf-8'))

    online = result['results']['online']
    offline = result['results']['offline']

    return (online, offline)

# Get offline agent's info
def OfflineAgentInfo(FLEET_URL, FLEET_PORT, FLEET_USERNAME, FLEET_PASSWORD):
    cmd = f'curl --insecure -X GET "https://{FLEET_URL}:{FLEET_PORT}/api/fleet/agents" -u "{FLEET_USERNAME}:{FLEET_PASSWORD}"'
    args = shlex.split(cmd)
    process = subprocess.Popen(args, shell=False, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    stdout, stderr = process.communicate()

    result = json.loads(stdout.decode('utf-8'))

    offline_agents = []
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

    return offline_agents

def SendAlertToTheHive(THEHIVE_SERVER, THEHIVE_PORT, THEHIVE_TOKEN, alert):
    cmd = f'curl -XPOST -H \'Authorization: Bearer {THEHIVE_TOKEN}\' -H \'Content-Type: application/json\' http://{THEHIVE_SERVER}:{THEHIVE_PORT}/api/alert -d \'\x7B  "title": "Offline Agents",  "description": "{alert}",  "type": "external",  "source": "instance-{str(datetime.now())}",  "sourceRef": "alert-ref"\x7D\''
    args = shlex.split(cmd)
    process = subprocess.Popen(args, shell=False, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    stdout, stderr = process.communicate()

def SendAlertToTelegram(TELEGRAM_TOKEN, TELEGRAM_ID, alert):
    alert = alert.replace("\\n\\r", "%0A")
    alert = alert.replace("\\t", "%09")
    alert = alert.replace("::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::", "%0A")
    cmd = f'curl -X POST "https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage" -d "chat_id={TELEGRAM_ID}&text={alert}"'
    
    args = shlex.split(cmd)
    process = subprocess.Popen(args, shell=False, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    stdout, stderr = process.communicate()

def main():
    alert = ""
    for i in config.FLEET_SERVERS:
        online, offline = AgentStatus(config.FLEET_SERVERS[i]["FLEET_URL"], config.FLEET_SERVERS[i]["FLEET_PORT"], config.FLEET_SERVERS[i]["FLEET_USERNAME"], config.FLEET_SERVERS[i]["FLEET_PASSWORD"])
        # alert += "=============================================================================================================================================================================\n"
        alert += "::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::\n"
        alert += f"FLEET_SERVER: {config.FLEET_SERVERS[i]['FLEET_URL']}\n\n"

        if offline == 0:
            alert += f"Agents online: {online},\t agent offline: {offline} ✅\n"
        else:
            alert += f"Agents online: {online},\t agent offline: {offline} ❌\n"
            alert += "Information of offline agents:\n"

        print(f"FLEET_SERVER: {config.FLEET_SERVERS[i]['FLEET_URL']}")
        print("Number of online agents: ", online)
        print("Number of offline agents: ", offline)

        offline_agents = OfflineAgentInfo(config.FLEET_SERVERS[i]["FLEET_URL"], config.FLEET_SERVERS[i]["FLEET_PORT"], config.FLEET_SERVERS[i]["FLEET_USERNAME"], config.FLEET_SERVERS[i]["FLEET_PASSWORD"])

        for i, agent in enumerate(offline_agents):
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
            alert += f"Last checkin: {last_checkin}\n\n"
        
        alert = alert.replace("\n", "\\n\\r")
        alert = alert.replace("\t", "\\t")
        alert = alert.replace("'", '\\"')
    
    SendAlertToTheHive(config.THEHIVE_SERVER, config.THEHIVE_PORT, config.THEHIVE_TOKEN, alert)
    SendAlertToTelegram(config.TELEGRAM_TOKEN, config.TELEGRAM_ID, alert)

main()
Footer
