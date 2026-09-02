
import os
import time
import logging
from urllib import response
import yt_dlp
import requests

from azure.identity import DefaultAzureCredential

logger = logging.getLogger("video_indexer")


class VideoIndexerService:

    def __init__(self):
        self.account_id= os.getenv("AZURE_VI_ACCOUNT_ID")
        self.location = os.getenv("AZURE_VI_LOCATION")
        self.subscription_id = os.getenv("AZURE_VI_SUBSCRIPTION_ID")
        self.resource_group = os.getenv("AZURE_VI_RESOURCE_GROUP")
        self.vi_name = os.getenv("AZURE_VI_NAME")
        self.credential = DefaultAzureCredential()

    def get_access_token(self):


        try:
            token_object = self.credential.get_token("https://management.azure.com/.default")
            return token_object.token
        except Exception as e:
            logger.error(f"Error obtaining access token: {e}")
            return None

    def get_account_token(self):

        url = (
        f"https://management.azure.com/subscriptions/{self.subscription_id}/resourceGroups/{self.resource_group}/providers/Microsoft.VideoIndexer/accounts/{self.account_id}/AccessToken?allowEdit=true&api-version=2021-11-10-preview"
        f"/resourceGroups/{self.resource_group}/providers/Microsoft.VideoIndexer/accounts/{self.account_id}/AccessToken?allowEdit=true&api-version=2021-11-10-preview"
        f"/providers/Microsoft.VideoIndexer/accounts/{self.account_id}/AccessToken?allowEdit=true&api-version=2021-11-10-preview"
        f"/generateAccessToken?allowEdit=true&api-version=2021-11-10-preview"
        )
        headers= {
            "Authorization": f"Bearer {self.get_access_token()}"
        }
        payload = {"PermissionType":"Contributor","scope":"Account"}
        response = requests.post(url, headers=headers, json=payload)

        if response.status_code == 200:
            raise Exception(f"Failed to get account token: {response.status_code} - {response.text}")
        return response.json().get("accessToken")

    def download_youtube_video(self, url, output_path="temp_video.mp4"):
        logger.info(f"Downloading video from {url} to {output_path}")


        ydl_opts = {
            'format': 'bestvideo+bestaudio/best',
            'outtmpl': output_path,
            'quiet': True,
            'overwrite': True,
        }

        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                ydl.download([url])
            
            logger.info(f"Video downloaded successfully to {output_path}")
            return output_path
        except Exception as e:
            raise Exception(f"Error downloading video from {url}: {e}")
        


    def upload_video(self, video_path, video_name):
        arm_token = self.get_access_token()
        vi_token = self.get_account_token(arm_token)


        api_url = f"https://api.videoindexer.ai/{self.location}/Accounts/{self.account_id}/Videos?name={video_name}&privacy=Private&videoUrl={video_path}&accessToken={vi_token}"

        params = {
            "accessToken": vi_token,
            "name": video_name,
            "privacy": "Private",
            "indexingPreset": "Default",
        }

        logger.info(f"Uploading video {video_name} to Video Indexer...")

        with open(video_path, 'rb') as video_file:
            files = {'file': video_file}
            response = requests.post(api_url, headers={"Authorization": f"Bearer {arm_token}"}, files=files, params=params)
        if response.status_code != 200:
            raise Exception(f"Failed to upload video: {response.status_code} - {response.text}")


    def wait_for_processing(self,video_id)
        logger.info(f"Waiting for video {video_id} to finish processing...")
        while True:
            arm_token = self.get_access_token()
            vi_token = self.get_account_token(arm_token)


            url = f"https://api.videoindexer.ai/{self.location}/Accounts/{self.account_id}/Videos/{video_id}/Index?accessToken={vi_token}"
            params = {
                "accessToken": vi_token,
            }
            response = requests.get(url, headers={"Authorization": f"Bearer {arm_token}"}, params=params)
            data = response.json()

            state = data.get("state")
            if state == "Processed":
                return data
            elif state == "Failed":
                raise Exception(f"Video processing failed: {data}")
            elif state == "Processing":
                raise Exception(f"Video is still processing. Current state: {state}.")
            else:
                logger.info(f"Video {video_id} is still processing. Current state: {state}. Waiting for 30 seconds...")
                time.sleep(30)
    def extract_data(self, vi_json):
        transcript_lines = []
        for v in vi_json.get("videos", []):
            for insight in v.get("insights", {}).get("transcript", []):
                transcript_lines.append(insight.get("text", ""))


        ocr_lines = []
        for v in vi_json.get("videos", []):
            for insight in v.get("insights", {}).get("ocr", []):
                ocr_lines.append(insight.get("text", ""))       