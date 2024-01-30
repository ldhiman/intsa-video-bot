import re
import requests
from bs4 import BeautifulSoup
import time

import hashlib
from uuid import uuid4
from datetime import datetime
import random
import threading
import time
from json import JSONDecodeError
import os
from video_generator import InstaVideoGenerator
import pickle  # Added for saving and loading sessions
from moviepy.video.io.VideoFileClip import VideoFileClip
import imageio
from plyer import notification
import json


def generate_thumbnail(video_path, output_path, time_in_seconds=5):
    try:
        # Load the video clip
        video_clip = VideoFileClip(video_path)

        # Get a frame at the specified time (in seconds)
        thumbnail_frame = video_clip.get_frame(time_in_seconds)

        # Save the thumbnail as an image file using imageio
        imageio.imwrite(output_path, thumbnail_frame)

        print(f"Thumbnail generated successfully at {output_path}")

    except Exception as e:
        print(f"An error occurred: {e}")


# Example Usage


# upload_reel(username, password, reel_path, caption)

from ensta import Host
import os


output_path = r"D:\Python\InstaVideoGenerator\output"


class InstaBot:
    def __init__(self, id, password):
        # self.browser = webdriver.Edge()
        self.id = id
        self.password = password
        self.cookies = {}
        self.insta_app_id = "936619743392459"
        # self.private_user_agent = ("Instagram 269.0.0.18.75 Android (26/8.0.0; 480dpi; 1080x1920; ""OnePlus; 6T Dev; devitron; qcom; en_US; 314665256)")
        self.private_user_agent = "Mozilla/5.0 (iPhone; CPU iPhone OS 15_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/15.0 Mobile/15E148 Safari/604.1"
        self.baseUrl = "https://www.instagram.com/"
        self.load_session()
        self.user_id = self.session.cookies.get("ds_user_id")
        self.insta_video_generator = InstaVideoGenerator()
        self.videos = [
            filename.split("_output")[0] for filename in os.listdir(output_path)
        ]

    def save_session(self):
        with open("session_cache.pkl", "wb") as f:
            pickle.dump(self.cookies, f)

    def load_session(self):
        try:
            with open("session_cache.pkl", "rb") as f:
                self.cookies = pickle.load(f)
                self.session = requests.Session()
                self.session.cookies.update(self.cookies)
        except FileNotFoundError:
            self.session = None
            self.loginReq()

    def upload_reel(self, title, path):
        host = Host(self.id, self.password)

        thumbnial_path = path.replace(".mp4", ".jpg")

        generate_thumbnail(path, thumbnial_path, time_in_seconds=2)

        host.upload_reel(video_path=path, thumbnail_path=thumbnial_path, caption=title)
        os.remove(thumbnial_path)
        print("uploaded!!")
        notification.notify(
            title="New Reel Uploaded!!",
            message=f"Your video is uploaded on instagram!!",
            app_name="Insta Reel Uploader",
        )

    def loginReq(self):
        link = self.baseUrl + "accounts/login/"
        login_url = self.baseUrl + "accounts/login/ajax/"

        time = int(datetime.now().timestamp())

        payload = {
            "username": self.id,
            "enc_password": f"#PWD_INSTAGRAM_BROWSER:0:{time}:{self.password}",  # <-- note the '0' - that means we want to use plain passwords
            "queryParams": {},
            "optIntoOneTap": "false",
        }

        with requests.Session() as s:
            r = s.get(link)
            csrf = re.findall(r"csrf_token\":\"(.*?)\"", r.text)[0]
            r = s.post(
                login_url,
                data=payload,
                headers={
                    "user-agent": self.private_user_agent,
                    "x-requested-with": "XMLHttpRequest",
                    "referer": "https://www.instagram.com/accounts/login/",
                    "x-csrftoken": csrf,
                },
            )
            print(r.status_code)
            print(r.json())
            if r.json().get("authenticated", False):
                self.user_id = r.json().get("user_id")

                r = s.get(self.baseUrl + "direct/inbox/")

                # Save cookies to cache
                self.cookies = {cookie.name: cookie.value for cookie in s.cookies}
                self.save_session()

                # Print cookies
                print("Cookies:")
                for cookie in s.cookies:
                    self.cookies[cookie.name] = cookie.value
                    print(f"{cookie.name}: {cookie.value}")
                self.session = s

            else:
                print("Login Failed!!")
                self.session = None

    @property
    def __private_headers(self) -> dict:
        try:
            mid = self.cookies["mid"]
        except JSONDecodeError:
            mid = ""

        return {
            "X-IG-App-Locale": "en_US",
            "X-IG-Device-Locale": "en_US",
            "X-IG-Mapped-Locale": "en_US",
            "X-Pigeon-Session-Id": f"UFS-{uuid4()}-1",
            "X-Pigeon-Rawclienttime": str(round(time.time(), 3)),
            "X-IG-Bandwidth-Speed-KBPS": str(random.randint(2500000, 3000000) / 1000),
            "X-IG-Bandwidth-TotalBytes-B": str(random.randint(5000000, 90000000)),
            "X-IG-Bandwidth-TotalTime-MS": str(random.randint(2000, 9000)),
            "X-IG-App-Startup-Country": "IN",
            "X-Bloks-Version-Id": "ce555e5500576acd8e84a66018f54a05720f2dce29f0bb5a1f97f0c10d6fac48",
            "X-IG-WWW-Claim": "0",
            "X-Bloks-Is-Layout-RTL": "false",
            "X-Bloks-Is-Panorama-Enabled": "true",
            "X-IG-Device-ID": str(uuid4()),
            "X-IG-Family-Device-ID": str(uuid4()),
            "X-IG-Android-ID": f"android-{hashlib.sha256(str(time.time()).encode()).hexdigest()[:16]}",
            "X-IG-Timezone-Offset": "-14400",
            "X-IG-Connection-Type": "WIFI",
            "X-IG-Capabilities": "3brTvx0=",
            "X-IG-App-ID": self.insta_app_id,
            "Priority": "u=3",
            "User-Agent": self.private_user_agent,
            "Accept-Language": "en-US",
            "X-MID": mid,
            "Accept-Encoding": "gzip, deflate",
            "Host": "i.instagram.com",
            "X-FB-HTTP-Engine": "Liger",
            "Connection": "keep-alive",
            "X-FB-Client-IP": "True",
            "X-FB-Server-Cluster": "True",
            "IG-INTENDED-USER-ID": self.user_id,
            "X-IG-Nav-Chain": "9MV:self_profile:2,ProfileMediaTabFragment:self_profile:3,9Xf:self_following:4",
            "X-IG-SALT-IDS": str(random.randint(1061162222, 1061262222)),
        }

    def inbox(self):
        if self.session is None:
            return

        http_response = self.session.get(
            "https://i.instagram.com/api/v1/direct_v2/inbox/",
            headers=self.__private_headers,
        )

        response_json: dict = http_response.json()

        if response_json.get("status", "") != "ok":
            print("Key 'status' not 'ok' in response json.")
            print(response_json)
            if response_json.get("require_login"):
                os.remove("session_cache.pkl")
                self.loginReq()
                self.inbox()
        if "inbox" not in response_json:
            print("Key 'inbox' not in response json.")

        inbox_json: dict = response_json.get("inbox", {})
        # Open a file in write mode
        with open("example.json", "w") as json_file:
            # Use json.dump to write the dictionary to the file
            json.dump(inbox_json, json_file)

        self.formatThings(inbox_json)

    def formatThings(self, inbox_json: dict):
        self.videos = [
            filename.split("_output")[0] for filename in os.listdir(output_path)
        ]
        unseen_count = inbox_json.get("unseen_count", None)

        threads = inbox_json.get("threads", None)

        print()
        if threads is not None:
            for thread in threads:
                # Extract thread information
                thread_id = thread.get("thread_id", "Unknown Thread ID")
                thread_v2_id = thread.get("thread_v2_id", "Unknown Thread V2 ID")

                users = thread.get("users", [])
                for user in users:
                    user_id = user.get("pk", "Unknown User ID")
                    full_name = user.get("full_name", "Unknown User")

                    print(f"Thread ID: {thread_id}")
                    print(f"Thread V2 ID: {thread_v2_id}")
                    print(f"User ID: {user_id}")
                    print(f"Full Name: {full_name}")

                last_activity_at = thread.get("last_activity_at", None)

                messages = thread.get("items", [])
                for message in messages:
                    # print(message)
                    item_id = message.get("item_id", "Unknown Item ID")
                    user_id = message.get("user_id", "Unknown User ID")
                    timestamp = message.get("timestamp", None)
                    item_type = message.get("item_type", "Unknown Item Type")
                    text = message.get("text", "No Text")
                    sent_by_other = not message.get("is_sent_by_viewer")
                    timestamp = message.get("timestamp", None)
                    print(f"Send by other: {sent_by_other}")
                    print(f"Item ID: {item_id}")
                    print(f"User ID: {user_id}")
                    print(f"Timestamp: {timestamp}")
                    print(f"Item Type: {item_type}")
                    if item_type == "text":
                        print(text)
                    else:
                        media_share = message.get(item_type, None)
                        if media_share.get("taken_at", None) is None:
                            media_share = media_share.get(item_type, None)
                        if media_share is not None:
                            media_type = media_share.get("media_type", None)
                            print(media_type)
                            if media_type == 2:
                                media_code = media_share.get("code", "no media code")
                                print(media_code)
                                if media_code in self.videos:
                                    continue
                                video_version = media_share.get("video_versions", [])
                                video_duration = media_share.get("video_duration", [])
                                download_able_url = None
                                for version in video_version:
                                    Type = version.get("type", 0)
                                    width = version.get("width", 0)
                                    height = version.get("height", 0)
                                    url = version.get("url", None)
                                    print(Type)
                                    print(width, height)
                                    print(url)
                                    download_able_url = url
                                path = self.insta_video_generator.generate_video(
                                    download_able_url, media_code, video_duration
                                )
                                self.upload_reel("New Reel!!", path)
                            else:
                                print(media_type)
                    print()
                print("-" * 50)

    def run(self):
            try:
                self.inbox()
            except Exception as e:
                os.remove("session_cache.pkl")
                print(e)
                self.inbox()


bot = InstaBot(#username, #password)
bot.run()
