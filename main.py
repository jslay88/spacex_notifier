import json
import os
from datetime import datetime, timedelta

import pytz
import requests


# Pushover settings
PUSHOVER_API_TOKEN = os.getenv("PUSHOVER_API_TOKEN")
PUSHOVER_USER_KEY = os.getenv("PUSHOVER_USER_KEY", os.getenv("PUSHOVER_GROUP_KEY"))

CACHE_PATH = os.getenv('CACHE_PATH', 'notified-launches.json')

# URL to fetch SpaceX launches
url = "https://fdo.rocketlaunch.live/json/launches/next/5"


def load_notified_launches():
    try:
        with open(CACHE_PATH, 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        return []


def save_notified_launches(notified_launches):
    with open(CACHE_PATH, 'w') as f:
        json.dump(notified_launches, f)


def has_notified(launch_id):
    return launch_id in load_notified_launches()


# Function to send Pushover notification
def send_pushover_notification(title, message):
    data = {
        'token': PUSHOVER_API_TOKEN,
        'user': PUSHOVER_USER_KEY,
        'title': title,
        'message': message,
    }
    requests.post("https://api.pushover.net/1/messages.json", data=data)


# Function to check if a launch is SpaceX and within the next hour
def check_launch_within_next_hour(launch):
    try:
        # Convert launch time (t0) to datetime object
        launch_time = datetime.strptime(launch['t0'], "%Y-%m-%dT%H:%MZ").replace(tzinfo=pytz.UTC)

        # Calculate current time and time 1 hour from now
        now = datetime.now(pytz.UTC)
        one_hour_from_now = now + timedelta(hours=1)

        # Check if the launch is SpaceX and within the next hour
        if now < launch_time <= one_hour_from_now:
            return True
    except Exception as e:
        print(f"Error checking launch time: {e}")

    return False


def main():
    # Perform the GET request
    response = requests.get(url)

    # Check if request was successful
    if response.status_code == 200:
        # Parse JSON response
        data = response.json()

        # Iterate through launches
        ids = []
        for launch in data.get('result', []):
            ids.append(launch['id'])
            # Check if the launch is SpaceX and within the next hour
            if (launch['provider']['name'] == 'SpaceX'
                    and check_launch_within_next_hour(launch)
                    and not has_notified(launch['id'])):
                # Prepare notification message
                title = f"SpaceX Launch Alert: {launch['name']}"
                message = f"{launch['launch_description']} - {launch['quicktext']}"

                # Send Pushover notification
                send_pushover_notification(title, message)

                save_notified_launches(load_notified_launches() + [launch['id']])

                # Print confirmation
                print(f"Notification sent for SpaceX launch: {launch['name']}")

        # Clear cache from launches that have passed
        notified_ids = load_notified_launches()
        for _id in notified_ids:
            if _id not in ids:
                notified_ids.remove(_id)
        save_notified_launches(notified_ids)

    else:
        print(f"Failed to retrieve data: {response.status_code} - {response.reason}")


if __name__ == '__main__':
    main()
