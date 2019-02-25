import requests
import time
import datetime
import sys
import json
import boto3

v2_metadata_endpoint = "http://169.254.170.2/v2/metadata"
v2_stats_endpoint = "http://169.254.170.2/v2/stats"
max_retries = 4
duration_between_retries = 1
cloudwatch = boto3.client('cloudwatch')

def metadata_response(endpoint):
    i = 0
    while i < max_retries:
        try:
            resp = requests.get(endpoint)
        except Exception as e:
            print e
        time.sleep(duration_between_retries)
        i = i + 1
    if resp != None:
        return resp
    else:
        return Exception

def task_metadata():
    task_metadata_resp = metadata_response(v2_metadata_endpoint)
    return task_metadata_resp.json()

def container_metadata(id):
    container_metadata_resp = metadata_response(v2_metadata_endpoint + "/" + id)
    return container_metadata_resp.json()

def task_stats():
    task_stats_resp = metadata_response(v2_stats_endpoint)
    return task_stats_resp.json()

def container_stats(id):
    container_stats_resp = metadata_response(v2_stats_endpoint + "/" + id)
    return container_stats_resp.json()

def put_metrics(metric_name, metric_value, container_id):
    if metric_name == "memory":
        unit = "Bytes"
    elif metric_name == "cpu":
        unit = "Percent"
    else:
        unit = "None"
    cloudwatch.put_metric_data(
        MetricData=[
            {
                'MetricName': metric_name,
                'Dimensions': [
                    {
                        'Name': 'Container ID',
                        'Value': container_id
                    }
                ],
                'Unit': unit,
                'Value': metric_value
            },
        ],
        Namespace='Fargate'
    )

print "starting", datetime.datetime.now()
time.sleep(5)
try:
    task_metadata_resp = task_metadata()
except Exception as e:
    print e
    exit()

print json.dumps(task_metadata_resp)

# TODO filter the pause container from the responses
# TODO create a list of container IDs
# TODO write loop that fetches Docker stats and outputs the stats to CloudWatch

'''Get the ID of a container'''
container_id = task_metadata_resp["Containers"][1]["DockerId"]

'''Get container metadata'''
container_metadata_resp = container_metadata(container_id)
print json.dumps(container_metadata_resp)

'''Get container stats'''
container_stats_resp = container_stats(container_id)
print json.dumps(container_stats_resp)

'''Get container memory usage'''
container_memory_usage = container_stats_resp["memory_stats"]["usage"]

'''Put memory metric to CloudWatch every 15 seconds'''
while True:
    container_stats_resp = container_stats(container_id)
    container_memory_usage = container_stats_resp["memory_stats"]["usage"]
    container_cpu_usage = container_stats_resp["cpu_stats"]["cpu_usage"]["total_usage"]
    put_metrics("memory",container_memory_usage,container_id)
    put_metrics("cpu",container_cpu_usage,container_id)
    time.sleep(15)