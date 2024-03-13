import websocket
import json
import threading
import os
import time


target_dir = 'target'
os.makedirs(target_dir, exist_ok=True)

def load_collection_ids(i):
    """
    Load collection IDs from a JSON file.
    """
    filename=f'./Collection_ids/{i}.json'
    with open(filename, 'r') as file:
        return json.load(file)

def on_message(ws, message):
    # Filter messages starting with '43'
    if message.startswith('43'):
        try:            
            # Find the position of '[' which marks the end of the status code
            json_start_pos = message.find('[')
            # Extract the status code based on its dynamic length
            if json_start_pos != -1:
                status_code = message[:json_start_pos].strip()
                file_name = f"{status_code}.json"
                full_file_path = os.path.join(target_dir, file_name)  # Construct the full file path

                json_content = message[json_start_pos:]
                data = json.loads(json_content)
                
                # Attempt to read the existing data, if any
                try:
                    with open(full_file_path, 'r') as file:
                        file_data = json.load(file)
                except (FileNotFoundError, json.JSONDecodeError):
                    # If the file does not exist or content is not valid JSON, start a new list
                    file_data = []
                
                # Append the new data
                file_data.append(data)
                
                # Write the updated data back to the file
                with open(full_file_path, 'w') as file:
                    json.dump(file_data, file, indent=4)

        except ValueError as e:
            print(f"Error parsing JSON from the message: {e}")

def on_error(ws, error):
    # print("Error:", error)
    pass

def on_close(ws, close_status_code, close_msg):
    # print("### closed ###")
    pass

def on_open(ws):
    def run(*args):
        j = 1
        for i in range(1,100):
            for collection in load_collection_ids(i):
                send_dynamic_message(ws, collection['id'], j)
                j += 1

    thread = threading.Thread(target=run)
    thread.start()

def send_dynamic_message(ws, collection_id, n):
    prefix = f"42{n}"
    message = [
    "get",
    {
        "method": "get",
        "data": {},
        "url": f"/request/?collection={collection_id}",
        "headers": {
        "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36 PostmanClient/10.24.1-240310-1628 (AppId=web)",
        "x-entity-team-id": "0",
        "x-app-version": "10.24.1-240310-1628"
        }
    }
    ]
    formatted_message = json.dumps(message)
    prefixed_message = f"{prefix}{formatted_message}"
    time.sleep(1)
    ws.send(prefixed_message)
    # print(f"Message sent for collection ID {collection_id}")

# Attempt to reconnect with an exponential backoff strategy
def reconnect_with_backoff(ws_url):
    backoff = 1  # Initial backoff duration in seconds
    max_backoff = 32  # Maximum backoff duration in seconds
    while True:
        try:
            print(f"Attempting to reconnect in {backoff}s")
            time.sleep(backoff)  # Delay before attempting to reconnect
            websocket.enableTrace(True)
            ws = websocket.WebSocketApp(ws_url,
                                        on_open=on_open,
                                        on_message=on_message,
                                        on_error=on_error,
                                        on_close=on_close)
            ws.run_forever(ping_timeout=30)  # Adjust ping_timeout as necessary
            break  # Exit the loop if run_forever returns without exception (connection closed gracefully)
        except websocket.WebSocketConnectionClosedException as e:
            print(f"Reconnect failed due to closed connection: {e}, retrying...")
        except Exception as e:
            print(f"Reconnect failed: {e}, retrying in {backoff}s")
        finally:
            backoff = min(backoff * 2, max_backoff)  # Exponential backoff

if __name__ == "__main__":
    ws_url = "wss://bifrost-web-v4.gw.postman.com/socket.io/?userId=28272125&teamId=0&os=Windows%2010&type=app_web&version=10.23.12-240308-0814&browser=Chrome%20122&__sails_io_sdk_version=1.2.1&__sails_io_sdk_platform=browser&__sails_io_sdk_language=javascript&EIO=3&transport=websocket"
    reconnect_with_backoff(ws_url)