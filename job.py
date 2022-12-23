import pathlib
import random
import string
from datetime import datetime, timedelta
from typing import Optional

import google.oauth2.credentials
import googleapiclient.discovery

import video_generation

from enum import Enum, auto

from config import Config


class Job:
	def __init__ (self, *,
			yt_url: str = "", speedup_factor: float = 1.8225, song_title: str = "", song_artist: str = ""):
		"""
		Creates a new job with a randomly generated ID, and a default status of Waiting.
		:param yt_url: The YouTube video to get audio from
		:param speedup_factor: The speedup factor for the audio
		:param song_title: The title of the song
		:param song_artist: The artist of the song
		"""
		self.id = "".join(random.choices(string.ascii_lowercase, k = 10))
		self.status = JobStatus.Waiting
		self.yt_url = yt_url
		self.speedup_factor = speedup_factor
		self.song_title = song_title
		self.song_artist = song_artist
		self.failure_info: Optional[str] = None

	def get_audio_location (self) -> str:
		"""
		:return: The absolute path to where the audio file should be located for this job
		"""
		return str(pathlib.Path.cwd().joinpath("data").joinpath(f"{self.id}.mp3"))

	def get_image_location (self) -> str:
		"""
		:return: The absolute path to where the image file should be located for this job
		"""
		return str(pathlib.Path.cwd().joinpath("data").joinpath(f"{self.id}.jpg"))

	def get_video_location (self) -> str:
		"""
		:return: The absolute path to where the video file should be saved for this job
		"""
		return str(pathlib.Path.cwd().joinpath("data").joinpath(f"{self.id}.mp4"))

	def cleanup_files (self) -> None:
		"""
		Deletes all the files for this job, and sets its status to deleted
		:return: None
		"""
		pathlib.Path(self.get_audio_location()).unlink(missing_ok = True)  # Unlink = remove file
		pathlib.Path(self.get_image_location()).unlink(missing_ok = True)
		pathlib.Path(self.get_video_location()).unlink(missing_ok = True)
		self.status = JobStatus.Deleted

	def check_ready (self) -> bool:
		"""
		Check if a job is ready to be run. To be ready, a YouTube link, speedup factor, song title, artist, and image
		must be provided.
		:return: True if job is ready, False otherwise
		"""
		return self.yt_url and self.song_title and self.song_artist and self.speedup_factor and \
			pathlib.Path(self.get_image_location()).exists()

	def run_job (self) -> None:
		"""
		Runs the job, returning once the video is done generating
		:return: None
		"""
		self.status = JobStatus.AudioProcessing
		video_generation.generate_audio(yt_url = self.yt_url,
										output_location = self.get_audio_location(),
										speedup_factor = self.speedup_factor)

		self.status = JobStatus.VideoProcessing
		video_generation.generate_video(audio_location = self.get_audio_location(),
										image_location = self.get_image_location(),
										save_location = self.get_video_location(),
										song_title = self.song_title,
										song_artist = self.song_artist)

		self.status = JobStatus.Done

	def set_youtube_info (self) -> bool:
		"""
		Sets the video name, description, and publish time of the video on YouTube
		:param publish_time: The time for the video to be published
		:return: None
		"""
		credentials = google.oauth2.credentials.Credentials(**Config.get("credentials"))
		youtube = googleapiclient.discovery.build("youtube", "v3", credentials = credentials)

		video_id_request = youtube.search().list(
			part = "snippet",
			forMine = True,
			maxResults = 1,
			q = f'"{self.id}"',
			type = "video"
		)

		video_id_response: dict = video_id_request.execute()

		video_id: str = video_id_response["items"][0]["id"]["videoId"]

		next_publish_date = datetime.fromisoformat(Config.get("next_publish_date"))

		get_details_request = youtube.videos().list(
			part = "status,snippet",
			id = video_id
		)

		video_details = get_details_request.execute()

		set_details_request = youtube.videos().update(
			part = "status,snippet",
			body = {
				"id":      video_id,
				"snippet": {
					"categoryId":      video_details["items"][0]["snippet"]["categoryId"],
					"description":     Config.get("description_format").format(title = self.song_title,
																			   artist = self.song_artist,
																			   yt_url = self.yt_url),
					"tags":            video_details["items"][0]["snippet"]["tags"],
					"title":           Config.get("title_format").format(title = self.song_title,
																		 artist = self.song_artist)
				},
				"status":  {
					"embeddable":              video_details["items"][0]["status"]["embeddable"],
					"license":                 video_details["items"][0]["status"]["license"],
					"privacyStatus":           "private",
					"publicStatsViewable":     video_details["items"][0]["status"]["publicStatsViewable"],
					"publishAt":               next_publish_date.isoformat(),
					"selfDeclaredMadeForKids": video_details["items"][0]["status"]["selfDeclaredMadeForKids"],
				}
			}
		)

		set_details_request.execute()

		next_publish_date += timedelta(hours = Config.get("publish_interval_hours"))
		Config.set("next_publish_date", next_publish_date.isoformat(timespec = "seconds"))

		self.status = JobStatus.Uploaded
		return True

	def __str__ (self):
		return f"{self.id} ({self.song_title})"

	def __eq__ (self, other):
		"""
		Checks if the ids of the jobs are equal
		"""
		return self.id == other.id


class JobStatus(Enum):
	Waiting = auto()
	Queued = auto()
	AudioProcessing = auto()
	VideoProcessing = auto()
	Done = auto()
	Uploaded = auto()
	Deleted = auto()
	Failed = auto()
