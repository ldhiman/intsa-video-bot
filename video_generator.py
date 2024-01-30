from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

from moviepy.editor import (
    VideoFileClip,
    ImageClip,
    CompositeVideoClip,
    concatenate_videoclips,
)

from PIL import Image

import joblib
from sklearn.feature_extraction.text import TfidfVectorizer
import os
import urllib.request
import requests
import numpy as np
import time


class InstaVideoGenerator:
    def __init__(self):
        # Load the saved model
        self.loaded_model = joblib.load("svm_model.joblib")
        self.vectorizer = joblib.load("tfidf_vectorizer.joblib")

        self.screenshot_path = r"D:\Python\InstaVideoGenerator\screenshot"
        self.video_path = r"D:\Python\InstaVideoGenerator\video"
        self.output_path = r"D:\Python\InstaVideoGenerator\output"

        if not os.path.exists(self.screenshot_path):
            os.mkdir(self.screenshot_path)
        if not os.path.exists(self.video_path):
            os.mkdir(self.video_path)
        if not os.path.exists(self.output_path):
            os.mkdir(self.output_path)

    def download_video(self, url, destination_path):
        try:
            with requests.get(url, stream=True) as response:
                response.raise_for_status()
                with open(destination_path, "wb") as file:
                    for chunk in response.iter_content(chunk_size=8192):
                        file.write(chunk)
            print(f"Video downloaded successfully to: {destination_path}")
            return destination_path
        except requests.exceptions.RequestException as e:
            print(f"Error downloading video: {e}")

    def string_to_dict(self, input_string):
        try:
            pairs = input_string.split(";")
            result_dict = {}
            for pair in pairs:
                key, value = pair.split("=")
                result_dict[key.strip()] = value.strip()
            return result_dict
        except Exception as e:
            print(f"Error converting string to dictionary: {e}")
            return None

    def generate_video(self, url, video_id, video_duration):
        screenshots = self.get_comments(video_id, video_duration)
        # print(screenshots)
        if len(screenshots) == 0:
            print("No comments available")
            return

        downloaded_video_path = self.download_video(
            url, f"{self.video_path}/{video_id}.mp4"
        )

        video_clip = VideoFileClip(downloaded_video_path)

        comment_duration = video_clip.duration / len(screenshots)
        margin_percentage = 0.1
        desired_width = int(video_clip.size[0] * (1 - margin_percentage))

        clips = []
        for i, screenshot in enumerate(screenshots):
            screenshot_image = Image.open(screenshot)
            screenshot_array = np.array(screenshot_image)
            aspect_ratio = screenshot_image.width / screenshot_image.height
            desired_height = int(desired_width / aspect_ratio)
            screenshot_clip = ImageClip(screenshot_array, duration=comment_duration)
            screenshot_clip = screenshot_clip.resize(
                width=desired_width, height=desired_height
            )
            screenshot_clip.set_opacity(0.8)
            screenshot_clip.set_position(("center", 0.7), relative=True)
            clips.append(screenshot_clip)

        content_overlay = concatenate_videoclips(clips).set_position(
            ("center", 0.7), relative=True
        )

        final_clip = CompositeVideoClip(
            clips=[video_clip, content_overlay], size=video_clip.size
        ).set_audio(video_clip.audio)

        final_clip.duration = video_clip.duration
        final_clip.set_fps(video_clip.fps)

        output_file = f"{self.output_path}/{video_id}_output.mp4"
        final_clip.write_videofile(
            output_file,
            codec="libx264",
            audio_codec="aac",
            threads="12",
            fps=24,
            bitrate="8000k",
            temp_audiofile="temp-audio.m4a",
            remove_temp=True,
        )

        print(f"Video with comments created: {output_file}")
        return output_file

    def get_comments(self, video_id, video_duration):
        # Set up headless WebDriver
        options = webdriver.EdgeOptions()
        # options.add_argument("--headless")
        options.add_argument(
            f"user-data-dir=C:\\Users\\Lucky\\AppData\\Local\\Microsoft\\Edge\\User Data"
        )

        self.driver = webdriver.Edge(options=options)
        filename = []
        url = f"https://www.instagram.com/p/{video_id}/"

        self.driver.get(url)

        if video_duration < 16:
            threshold = video_duration / 3
        else:
            threshold = video_duration / 5
        print(f"Comment Threshold: {threshold}")

        WebDriverWait(self.driver, 30).until(
            EC.presence_of_element_located(
                (
                    By.XPATH,
                    "/html/body/div[2]/div/div/div[2]/div/div/div[1]/div[1]/div[2]/section/main/div/div[1]/div/div[2]/div/div[2]/div/div[2]",
                )
            )
        )

        elem = self.driver.find_element(
            By.XPATH,
            "/html/body/div[2]/div/div/div[2]/div/div/div[1]/div[1]/div[2]/section/main/div/div[1]/div/div[2]/div/div[2]/div/div[2]",
        )

        comments = elem.find_elements(
            By.XPATH,
            "div",
        )
        print(f"Total Comments: {len(comments)}")

        filename = self.capture_screenshot(
            comments, video_id, filename, elem, threshold
        )

        if len(filename) == 0:
            comment = comments[1]
            path = f"{self.screenshot_path}/{id}_{0}.png"
            comment.screenshot(path)
            filename.append(path)

        self.driver.close()
        return filename

    def capture_screenshot(self, comments, video_id, filename, elem, threshold):
        i = 1
        for comment in comments[1:]:
            try:
                # Scroll to the comment element
                self.driver.execute_script(
                    "arguments[0].scrollIntoView(true);", comment
                )
                time.sleep(1)  # Add a delay to ensure the comment is fully loaded

                comment_text = comment.find_elements(
                    By.CSS_SELECTOR,
                    "span.x1lliihq.x1plvlek.xryxfnj.x1n2onr6.x193iq5w.xeuugli.x1fj9vlw.x13faqbe.x1vvkbs.x1s928wv.xhkezso.x1gmr53x.x1cpjm7i.x1fgarty.x1943h6x.x1i0vuye.xvs91rp.xo1l8bm.x5n08af.x10wh9bi.x1wdrske.x8viiok.x18hxmgj",
                )[1].text

                new_text_tfidf = self.vectorizer.transform([comment_text])
                prediction = self.loaded_model.predict(new_text_tfidf)

                if prediction >= 0:
                    print(comment_text)
                    path = f"{self.screenshot_path}/{video_id}_{i}.png"
                    # comment.screenshot(path)
                    fp = open(path, "wb")
                    fp.write(comment.screenshot_as_png)
                    fp.close()
                    filename.append(path)
                    i += 1
            except IndexError as e:
                print()

        if len(filename) < threshold:
            self.driver.execute_script(
                "arguments[0].scrollIntoView(true);", comments[-1]
            )
            # Wait for the number of comments to increase
            WebDriverWait(self.driver, 20).until(
                lambda driver: len(elem.find_elements(By.XPATH, "div")) > len(comments)
            )
            comments = elem.find_elements(
                By.XPATH,
                "div",
            )
            print(f"Total Comments: {len(comments)}")
            return self.capture_screenshot(comments, video_id, [], elem, threshold)

        return filename


if __name__ == "__main__":
    insta_video_generator = InstaVideoGenerator()
    insta_video_generator.generate_video(
        "https://scontent-del2-1.cdninstagram.com/o1/v/t16/f1/m69/GEX_vgJlb29DSngBAMOnSxOOr7gKbpR1AAAF.mp4?efg=eyJxZV9ncm91cHMiOiJbXCJpZ193ZWJfZGVsaXZlcnlfdnRzX290ZlwiXSIsInZlbmNvZGVfdGFnIjoidnRzX3ZvZF91cmxnZW4uY2xpcHMuYzIuMTA4MC5oaWdoIn0&_nc_ht=scontent-del2-1.cdninstagram.com&_nc_cat=111&vs=694892886128426_2749467941&_nc_vs=HBksFQIYOnBhc3N0aHJvdWdoX2V2ZXJzdG9yZS9HRVhfdmdKbGIyOURTbmdCQU1PblN4T09yN2dLYnBSMUFBQUYVAALIAQAVAhg6cGFzc3Rocm91Z2hfZXZlcnN0b3JlL0dMWnlUaE1wdTNCZk1hMFpBSnlMWGpjeHZjbHNicFIxQUFBRhUCAsgBACgAGAAbABUAACbssKmBgq31PxUCKAJDMywXQDgqfvnbItEYEmRhc2hfaGlnaF8xMDgwcF92MREAdf4HAA%3D%3D&ccb=9-4&oh=00_AfBEf-32SzOZ7iZ7GSwondhOKrSeUywwwLt4uOtN4-EV9Q&oe=65B80B46&_nc_sid=b1bb43",
        "C2mlQtVvXzF",
        10,
    )
    insta_video_generator.close_driver()
