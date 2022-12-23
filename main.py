import threading
import time

import flask
import jsonpickle
from flask import Flask, render_template, send_file, request, redirect, url_for

import google_auth_oauthlib.flow

import image_generation
from job import Job, JobStatus
from job_manager import JobManager
from config import Config

app = Flask(__name__)

job_manager = JobManager(True)


# Start up a thread that saves the state every 30 minutes
# def save_timer ():
# 	time.sleep(1800)
# 	job_manager.save_state()
#
#
# threading.Thread(target = save_timer, daemon = True)


# -- MISC --

@app.route("/")
def main_page ():
	job_counts = job_manager.get_counts()

	return render_template("index.html", job_counts = job_counts)


@app.route("/settings", methods = ["GET", "POST"])
def settings ():
	file_upload_success = None
	google_login_success = None

	# Config file uploaded
	if request.method == "POST" and "config-file" in request.files:
		config_file = request.files["config-file"]

		if not config_file.filename.endswith(".json"):
			file_upload_success = False
		else:
			# noinspection PyBroadException
			try:
				config_file.save("config.json")
				Config.reload_config()
				file_upload_success = True
			except Exception:
				file_upload_success = False

	if "google_login_success" in request.args:
		if request.args["google_login_success"] == "true":
			google_login_success = True
		else:
			google_login_success = False

	job_counts = job_manager.get_counts()

	return render_template("settings.html", job_counts = job_counts, file_upload_success = file_upload_success,
						   google_login_success = google_login_success)


@app.route("/settings/download")
def download_config ():
	return send_file("config.json", as_attachment = True)


@app.route("/google-login")
def google_login ():
	if "code" in request.args:  # After login attempt, success
		flow = google_auth_oauthlib.flow.Flow.from_client_secrets_file(
			"client_secret.json",
			scopes = ["https://www.googleapis.com/auth/youtube.force-ssl"],
			state = Config.get("state")
		)
		flow.redirect_uri = "http://localhost:8080/google-login"

		flow.fetch_token(code = request.args["code"])

		credentials = flow.credentials

		credentials_dict = {"token":         credentials.token,
							"refresh_token": credentials.refresh_token,
							"token_uri":     credentials.token_uri,
							"client_id":     credentials.client_id,
							"client_secret": credentials.client_secret,
							"scopes":        credentials.scopes}

		Config.set("credentials", credentials_dict)

		Config.set("state", "")

		return flask.redirect(url_for("settings", google_login_success = "true"))

	elif "error" in request.args:  # After login attempt, failure
		return flask.redirect(url_for("settings", google_login_success = "false"))

	else:  # Before login attempt
		flow = google_auth_oauthlib.flow.Flow.from_client_secrets_file(
			"client_secret.json",
			scopes = ["https://www.googleapis.com/auth/youtube.force-ssl"]
		)

		flow.redirect_uri = "http://localhost:8080/google-login"

		authorization_url, state = flow.authorization_url(
			access_type = "offline",
			include_granted_scopes = "true"
		)

		Config.set("state", state)

		return flask.redirect(authorization_url)


@app.route("/favicon.ico")
def favicon ():
	return send_file("./nightnightcore.ico")


@app.route("/save")
def save ():
	job_manager.save_state()
	return "true"


# -- JOBS --

@app.route("/jobs")
def list_jobs ():
	job_statues: list[JobStatus] = []
	request_terms: list[str] = []
	if "types" in request.args:
		request_terms = request.args["types"].split(",")
		if request_terms == [""]:
			request_terms = []
		for job_type in request_terms:
			if job_type == "waiting":
				job_statues.append(JobStatus.Waiting)
			elif job_type == "queued":
				job_statues.append(JobStatus.Queued)
			elif job_type == "processing":
				job_statues.extend((JobStatus.AudioProcessing, JobStatus.VideoProcessing))
			elif job_type == "done":
				job_statues.append(JobStatus.Done)
			elif job_type == "uploaded":
				job_statues.append(JobStatus.Uploaded)
			elif job_type == "failed":
				job_statues.extend((JobStatus.Failed, JobStatus.Deleted))

	filter_button_types: dict[str, list[str]] = {}
	for request_term in ("waiting", "queued", "processing", "done", "uploaded", "failed"):
		if request_term in request_terms:
			filter_button_types[request_term] = [term for term in request_terms if term != request_term]
		else:
			filter_button_types[request_term] = request_terms + [request_term]

	job_counts = job_manager.get_counts()

	jobs = job_manager.get_jobs_with_status(*job_statues)

	return render_template("jobs.html", request_terms = request_terms, job_counts = job_counts, jobs = jobs,
						   filter_button_types = filter_button_types, JobStatus = JobStatus)


@app.route("/job/<job_id>")
def job_page (job_id: str):
	job = job_manager.jobs[job_id]
	return jsonpickle.encode(job)


@app.route("/job/<job_id>/image")
def get_job_image (job_id: str):
	return send_file(job_manager.jobs[job_id].get_image_location())


@app.route("/job/<job_id>/audio")
def get_job_audio (job_id: str):
	return send_file(job_manager.jobs[job_id].get_audio_location(), as_attachment = True)


@app.route("/job/<job_id>/video")
def get_job_video (job_id: str):
	return send_file(job_manager.jobs[job_id].get_video_location(), as_attachment = True)


@app.route("/job/<job_id>/queue")
def queue_job (job_id: str):
	if job_manager.queue_job(job_id):
		return "true"
	else:
		return "false"


@app.route("/job/queue-all")
def queue_all_ready ():
	job_manager.queue_all_ready_waiting()
	return "true"


@app.route("/job/<job_id>/dequeue")
def dequeue_job (job_id: str):
	if job_manager.dequeue_job(job_id):
		return "true"
	else:
		return "false"


@app.route("/job/<job_id>/delete")
def delete_job (job_id: str):
	if job_manager.delete_job(job_id):
		return "true"
	else:
		return "false"


@app.route("/job/<job_id>/set_youtube_info")
def set_youtube_info (job_id: str):
	if job_manager.jobs[job_id].set_youtube_info():
		return "true"
	else:
		return "false"


@app.route("/job/set_youtube_info_all")
def set_youtube_info_all ():
	any_failures = False
	for job in job_manager.jobs.values():
		if job.status == JobStatus.Done:
			if not job.set_youtube_info():
				any_failures = True

	if not any_failures:
		return "true"
	else:
		return "false"


@app.route("/new-job")
def create_job ():
	job_id = job_manager.add_job(Job())
	try:
		image_generation.get_random_image_from_web(job_manager.jobs[job_id].get_image_location())
	except Exception as exception:
		print(exception)
	return redirect(url_for("job_page", job_id = job_id))


# -- QUEUE --

@app.route("/queue")
def queue_status ():
	job_counts = job_manager.get_counts()

	queue = job_manager.get_queue()

	return render_template("queue.html", job_counts = job_counts, queue = queue, JobStatus = JobStatus)


# -- JAVASCRIPT FILES --

@app.route("/js/navbar")
def navbar_js ():
	return render_template("navbar.js")


@app.route("/js/jobs")
def jobs_js ():
	return render_template("jobs.js")


@app.route("/js/settings")
def settings_js ():
	return render_template("settings.js")
