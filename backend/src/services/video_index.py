
import os
import time
import logging
from urllib import response
from langchain_openai import data
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
        f"https://management.azure.com/subscriptions/{self.subscription_id}"
        f"/resourceGroups/{self.resource_group}"
        f"/providers/Microsoft.VideoIndexer/accounts/{self.vi_name}"
        f"/generateAccessToken"
        f"?api-version=2025-04-01"
    )

        arm_token = self.get_access_token()

        if not arm_token:
            raise Exception("Could not obtain Azure ARM access token.")

        headers = {
        "Authorization": f"Bearer {arm_token}",
        "Content-Type": "application/json",
    }

        payload = {
        "permissionType": "Contributor",
        "scope": "Account",
    }

        response = requests.post(
        url,
        headers=headers,
        json=payload,
        timeout=30,
    )

        if response.status_code != 200:
            raise Exception(
            f"Failed to get Video Indexer access token: "
            f"{response.status_code} - {response.text}"
        )

        vi_token = response.json().get("accessToken")

        if not vi_token:
            raise Exception("Video Indexer response did not contain accessToken.")

        logger.info("Successfully obtained Video Indexer account access token.")

        return vi_token

    def download_youtube_video(self, video_url):
        output_path = os.path.abspath("tem_audit_video")

        ydl_opts = {
    "format": "bestvideo*+bestaudio/best",
    "remote_components": ["ejs:github"],
    "outtmpl": output_path + ".%(ext)s",
    "quiet": True,
    "overwrites": True,
    "merge_output_format": "mp4",
}

        logger.info(f"Downloading video from {video_url}")

        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(video_url, download=True)
            downloaded_path = ydl.prepare_filename(info)

        logger.info(f"Video downloaded successfully to {downloaded_path}")

        return downloaded_path


    def upload_video(self, video_path, video_name):

        vi_token = self.get_account_token()

        api_url = (
        f"https://api.videoindexer.ai/{self.location}"
        f"/Accounts/{self.account_id}/Videos"
    )

        params = {
        "accessToken": vi_token,
        "name": video_name,
        "privacy": "Private",
        "indexingPreset": "Default",
    }

        logger.info(f"Uploading video {video_name} to Video Indexer...")

        with open(video_path, "rb") as video_file:

            files = {
            "file": video_file
        }

            response = requests.post(
            api_url,
            files=files,
            params=params,
            timeout=300,
        )

        if response.status_code not in (200, 201):
            raise Exception(
            f"Failed to upload video: "
            f"{response.status_code} - {response.text}"
        )

        data = response.json()

        video_id = data.get("id")

        if not video_id:
            raise Exception(
            f"Upload succeeded but Video Indexer returned no video ID: {data}"
        )

        logger.info(
        f"Video uploaded successfully. Video ID: {video_id}"
    )

        return video_id


    def wait_for_processing(self, video_id):

        logger.info(
        f"Waiting for video {video_id} to finish processing..."
    )

        while True:

            vi_token = self.get_account_token()

            url = (
            f"https://api.videoindexer.ai/{self.location}"
            f"/Accounts/{self.account_id}"
            f"/Videos/{video_id}/Index"
        )

            params = {
            "accessToken": vi_token,
        }

            response = requests.get(
            url,
            params=params,
            timeout=30,
        )

            if response.status_code != 200:
                raise Exception(
                f"Failed to get video status: "
                f"{response.status_code} - {response.text}"
            )

            data = response.json()

            state = data.get("state")

            logger.info(
            f"Video {video_id} current state: {state}"
        )

            if state == "Processed":
                logger.info("Video processing completed.")

                return data

            elif state == "Failed":
                raise Exception(
                f"Video processing failed: {data}"
            )

            else:
                logger.info(
                "Video is still processing. Waiting 30 seconds..."
            )
                time.sleep(30)
    def get_video_insights(self, video_id):
        """Retrieve processed video insights from Azure Video Indexer."""

        vi_token = self.get_account_token()

        url = (
        f"https://api.videoindexer.ai/{self.location}"
        f"/Accounts/{self.account_id}"
        f"/Videos/{video_id}/Index"
    )

        params = {
        "accessToken": vi_token,
    }

        logger.info(
        f"Getting insights for Video Indexer video: {video_id}"
    )

        response = requests.get(
        url,
        params=params,
        timeout=60,
    )

        if response.status_code != 200:
            raise Exception(
            f"Failed to get video insights: "
            f"{response.status_code} - {response.text}"
        )

        data = response.json()

        logger.info(
        f"Successfully retrieved insights for video {video_id}"
    )

        return data
    def extract_data(self, vi_json):
        transcript_lines = []
        for v in vi_json.get("videos", []):
            for insight in v.get("insights", {}).get("transcript", []):
                transcript_lines.append(insight.get("text", ""))


        ocr_lines = []
        for v in vi_json.get("videos", []):
            for insight in v.get("insights", {}).get("ocr", []):
                ocr_lines.append(insight.get("text", ""))       
        return {
            "transcript": transcript_lines,
            "ocr": ocr_lines,
        }
