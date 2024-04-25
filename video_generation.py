import subprocess
import os
import threading
import time
from typing import Callable, Any

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support import expected_conditions
from selenium.webdriver.support.ui import WebDriverWait

from yt_dlp import YoutubeDL

from config import Config

options = webdriver.ChromeOptions()
options.binary_location = Config.get("chrome_location")

# We can't distinguish between dialog boxes created by different programs, so create a lock so only one thread can have
# a dialog box open at one time
ahk_lock = threading.Lock()


def generate_audio (*, yt_url: str, speedup_factor: float = 1.8225, output_location: str) -> None:
	"""
	Downloads the audio of the linked YouTube video, speeds it up by the given factor using ffmpeg, and then saves it to
	the given output location
	:param yt_url: The YouTube video to get audio from
	:param speedup_factor: The speedup factor, by default 1.8225
	:param output_location: The location to save the resulting audio file
	:return: None
	"""
	try:
		# Download audio
		ytdl_options = {
			"format":  "bestaudio",
			"outtmpl": f"{output_location}.temp.webm"
		}
		with YoutubeDL(ytdl_options) as ytdl:
			ytdl.download([yt_url])

		# Get sample rate of downloaded audio
		ffprobe = subprocess.run([Config.get("ffprobe_location"), "-v", "error", "-show_entries", "stream=sample_rate",
								  "-of", "default=noprint_wrappers=1:nokey=1", f"{output_location}.temp.webm"],
								 stdout = subprocess.PIPE)

		# Speed up the audio and save it
		subprocess.call([Config.get("ffmpeg_location"), "-y", "-i", f"{output_location}.temp.webm", "-filter:a",
						 f"asetrate={ffprobe.stdout.decode('utf-8').strip()}*{speedup_factor}", output_location])
	finally:
		# Delete the temporary file
		os.remove(f"{output_location}.temp.webm")


def generate_video (*, song_title: str, song_artist: str, audio_location: str, image_location: str,
		save_location: str, progress_callback: Callable[[str], Any] = lambda _: None) -> None:
	"""
	Given a set of parameters, generates a music visualiser video using vizzy.io
	:param song_title: The name of the song that will appear in the video
	:param song_artist: The name of the artist that will appear in the video
	:param audio_location: The absolute path to an audio file that will be used as the audio of the video
	:param image_location: The absolute path to an image that will be used as the background of the video
	:param save_location: The absolute path the resulting video will be saved to
	:param progress_callback: A function which will be called with the progress text to update the job's project
	:return: None
	"""
	browser = webdriver.Chrome(options = options)
	wait = WebDriverWait(browser, 20)

	# Load page with template
	browser.get(Config.get("template_url"))

	# Wait until page finishes loading
	wait.until(expected_conditions.invisibility_of_element_located((By.XPATH, '//*[@id="root"]/div[1]/div')))

	# Dismiss cookie banner
	wait.until(expected_conditions.element_to_be_clickable((By.CLASS_NAME, "cc-nb-reject")))
	browser.find_element(By.CLASS_NAME, "cc-nb-reject").click()

	# -- VIDEO CUSTOMISATION --

	# Set resolution to 1080p
	wait.until(expected_conditions.element_to_be_clickable((By.XPATH, '//span[text()="1080"]')))
	browser.find_element(By.XPATH, '//span[text()="1080"]').click()

	# Select image
	wait.until(expected_conditions.element_to_be_clickable((By.XPATH, '//span[text()="Image Background"]')))
	browser.find_element(By.XPATH, '//span[text()="Image Background"]').click()

	# Get the source of the image element, so we can tell when it changes later
	image_src = browser.find_element(By.XPATH, '//img[contains(@src, "firebasestorage")]').get_attribute("src")

	# Fill image
	browser.find_element(By.XPATH, '//input[@id="image-upload-button"]').send_keys(image_location)

	# Wait for image to load
	wait.until(expected_conditions.invisibility_of_element_located((By.XPATH, f'//img[@src="{image_src}"]')))

	# Select song title
	wait.until(expected_conditions.element_to_be_clickable((By.XPATH, '//span[text()="Song Title"]')))
	browser.find_element(By.XPATH, '//span[text()="Song Title"]').click()

	# Fill song title
	song_title_element = browser.find_element(By.XPATH, '//textarea[text()="Placeholder Title"]')
	song_title_element.send_keys(Keys.CONTROL + "a")
	song_title_element.send_keys(Keys.DELETE)
	song_title_element.send_keys(song_title)

	# Select song artist
	wait.until(expected_conditions.element_to_be_clickable((By.XPATH, '//span[text()="Artist Name"]')))
	browser.find_element(By.XPATH, '//span[text()="Artist Name"]').click()

	# Fill song artist
	song_artist_element = browser.find_element(By.XPATH, '//textarea[text()="Placeholder Artist"]')
	song_artist_element.send_keys(Keys.CONTROL + "a")
	song_artist_element.send_keys(Keys.DELETE)
	song_artist_element.send_keys(song_artist)

	# -- SIGN IN --

	# Click sign in button
	wait.until(expected_conditions.element_to_be_clickable((By.XPATH, '//span[text()="Sign in"]')))
	browser.find_element(By.XPATH, '//span[text()="Sign in"]').click()

	# Fill email
	browser.find_element(By.XPATH, '//input[@name="email"]').send_keys(Config.get("vizzy_email"))

	# Fill password
	browser.find_element(By.XPATH, '//input[@name="password"]').send_keys(Config.get("vizzy_password"))

	# Click submit button
	wait.until(expected_conditions.element_to_be_clickable((By.XPATH, '//span[text()="Sign In"]')))
	browser.find_element(By.XPATH, '//span[text()="Sign In"]').click()

	# Wait until signed-in
	wait.until(expected_conditions.invisibility_of_element_located((By.XPATH, '/html/body/div[3]/div[3]/div/div')))

	# -- AUDIO SELECTION --

	# Only allow one thread to open a dialog box at a time
	with ahk_lock:
		# Click on select audio button
		wait.until(expected_conditions.element_to_be_clickable((By.XPATH, '//span[text()="Choose audio"]')))
		browser.find_element(By.XPATH, '//span[text()="Choose audio"]').click()

		# Select audio file
		subprocess.call([Config.get("autohotkey_location"), Config.get("openfile_ahk_script"), audio_location])

	# Wait until audio finishes processing
	wait.until(expected_conditions.visibility_of_element_located((By.XPATH, '//h4[text()="Analyzing audio..."]')))
	wait.until(expected_conditions.invisibility_of_element_located((By.XPATH, '//h4[text()="Analyzing audio..."]')))

	# -- EXPORT --

	# Select File from the menu bar
	wait.until(expected_conditions.element_to_be_clickable((By.XPATH, '//span[text()="File"]')))
	browser.find_element(By.XPATH, '//span[text()="File"]').click()

	# Select Export from the menu
	wait.until(expected_conditions.element_to_be_clickable((By.XPATH, '//li[@id="export"]')))
	browser.find_element(By.XPATH, '//li[@id="export"]').click()

	# Delete advertisement, to make sure the progress percentage is on screen
	browser.execute_script("""
var element = arguments[0];
element.parentNode.removeChild(element);
""", browser.find_element(By.XPATH, '//*[@id="root"]/div/div/div[1]/div'))

	# Show advanced settings
	wait.until(expected_conditions.element_to_be_clickable((By.XPATH, '//p[text()="Show advanced settings"]')))
	browser.find_element(By.XPATH, '//p[text()="Show advanced settings"]').click()

	# Use file system
	filesystem_checkbox = browser.find_element(By.XPATH, '//input[@type="checkbox"]')
	browser.execute_script("arguments[0].click();", filesystem_checkbox)

	# Only allow one thread to open a dialog box at a time
	with ahk_lock:
		# Start export
		wait.until(expected_conditions.element_to_be_clickable((By.XPATH, '//span[text()="Start export"]')))
		browser.find_element(By.XPATH, '//span[text()="Start export"]').click()

		# Select export location
		subprocess.call([Config.get("autohotkey_location"), Config.get("savefile_ahk_script"), save_location])

	# Wait for export to start
	while (progress_text := browser.find_element(By.XPATH, '//*[@id="root"]/div/div/div[2]/div[2]/div[2]/h6').text) \
			== "0%":
		progress_callback(progress_text)
		time.sleep(2)

	# Wait for export to finish
	while (progress_text := browser.find_element(By.XPATH, '//*[@id="root"]/div/div/div[2]/div[2]/div[2]/h6').text) \
			!= "0%":
		progress_callback(progress_text)
		time.sleep(2)

	# Wait a little longer
	time.sleep(2)

	# Quit
	browser.quit()
