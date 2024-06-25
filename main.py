import requests
from datetime import datetime, timedelta
import pytz  # pip install pytz
import os

# Pushover settings
PUSHOVER_API_TOKEN = os.getenv("PUSHOVER_API_TOKEN")
PUSHOVER_USER_KEY = os.getenv("PUSHOVER_USER_KEY", os.getenv("PUSHOVER_GROUP_KEY"))

# URL to fetch SpaceX launches
url = "https://fdo.rocketlaunch.live/json/launches/next/5"


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
        for launch in data.get('result', []):
            # Check if the launch is SpaceX and within the next hour
            if launch['provider']['name'] == 'SpaceX' and check_launch_within_next_hour(launch):
                # Prepare notification message
                title = f"SpaceX Launch Alert: {launch['name']}"
                message = f"{launch['launch_description']} - {launch['quicktext']}"

                # Send Pushover notification
                send_pushover_notification(title, message)

                # Print confirmation
                print(f"Notification sent for SpaceX launch: {launch['name']}")
                break  # Exit loop after sending first notification (if multiple launches are within the hour)
        else:
            print("No SpaceX launches found within the next hour.")
    else:
        print(f"Failed to retrieve data: {response.status_code} - {response.reason}")


if __name__ == '__main__':
    main()
