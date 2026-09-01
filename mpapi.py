import sys
import socket
from multiprocessing import Process, Queue
from multiprocessing.connection import Client, Listener
import urllib.request
import urllib.error
from array import array
import json
import time


def server_fun(localPort, queue):
    # Set the address of the local node's server
    localServerAddress = ("localhost", localPort)

    # Send fixed message
    # with Listener(localServerAddress, authkey=b'Lets work together') as listener:
    with Listener(localServerAddress) as listener:  # without authentication

        while True:
            with listener.accept() as conn:
                # print('connection accepted from', listener.last_accepted)
                bmsg = conn.recv()
                msg = json.loads(bmsg)
                # print(msg)

                # Forward msg to local node's process
                queue.put(msg)

                # Exit if msg is 'exit'
                if msg == "exit":
                    break


def sendMsg(remoteServerAddress, msg):
    MAX_RETRY_COUNT = 100
    counter = 0
    while counter < MAX_RETRY_COUNT:
        try:
            # with Client(remoteServerAddress, authkey=b'Lets work together') as conn:
            with Client(remoteServerAddress) as conn:  # without authentication
                bmsg = json.dumps(msg).encode("utf-8")
                conn.send(bmsg)
                break
        except OSError as e:  # former socket.error exception
            print(
                f"Modlule msg_passing_api, Function sendMsg: An exectption {e} occured, the operation will be retried..."
            )
            # This was tested with apps with up to 200 nodes, on Dell Latitude 3420 laptop. Be sure to exit all apps and disconnect from Internet.
            time.sleep(0.2)  # wait for 200 ms
            counter += 1
    if counter >= MAX_RETRY_COUNT:
        sys.exit()


def rcvMsg(queue):
    return queue.get()


def broadcastMsg(listOfRemoteServerAddress, msg):
    for remoteServerAddress in listOfRemoteServerAddress:
        sendMsg(remoteServerAddress, msg)


def rcvMsgs(queue, noOfMessagesToReceive):
    msgs = []

    for i in range(noOfMessagesToReceive):
        msgs.append(rcvMsg(queue))

    return msgs


default_headers = {"Content-Type": "application/json", "Accept": "application/json"}


def http_post(url: str, json_data: dict):
    """
    Sends a POST request to the specified URL with the provided JSON payload.

    Args:
        url (str): The endpoint to send the request to.
        json_data (dict): The JSON data to include in the request body.

    Returns:
        Parsed JSON response if successful, None otherwise.
    """
    try:
        data = json.dumps(json_data).encode("utf-8")
        request = urllib.request.Request(
            url, data=data, headers=default_headers, method="POST"
        )
        with urllib.request.urlopen(request) as response:
            response_data = response.read().decode("utf-8")
            return json.loads(response_data)
    except (urllib.error.URLError, urllib.error.HTTPError, json.JSONDecodeError) as e:
        print(
            f"Warning: POST request to {url} failed or response is not valid JSON: {e}"
        )
        return None


def http_get(url: str):
    """
    Sends a GET request to the specified URL.

    Args:
        url (str): The endpoint to send the request to.

    Returns:
        Parsed JSON response if successful, None otherwise.
    """
    try:
        request = urllib.request.Request(url, headers=default_headers, method="GET")
        with urllib.request.urlopen(request) as response:
            response_data = response.read().decode("utf-8")
            return json.loads(response_data)
    except (urllib.error.URLError, urllib.error.HTTPError, json.JSONDecodeError) as e:
        print(
            f"Warning: GET request to {url} failed or response is not valid JSON: {e}"
        )
        return None