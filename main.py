import threading
import time

import jsonpickle
from flask import Flask, render_template, send_file, request, redirect, url_for

import image_generation
from job import Job, JobStatus
from job_manager import JobManager

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


@app.route("/settings")
def settings ():
	return "Settings"


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
	return send_file(job_manager.jobs[job_id].get_audio_location())


@app.route("/job/<job_id>/video")
def get_job_video (job_id: str):
	return send_file(job_manager.jobs[job_id].get_video_location())


@app.route("/job/<job_id>/queue")
def queue_job (job_id: str):
	if job_manager.queue_job(job_id):
		return "true"
	else:
		return "false"


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
	if job_manager.jobs[job_id].set_youtube_info("x"):
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
	return "Queue"


# -- JAVASCRIPT FILES --

@app.route("/js/navbar")
def navbar_js ():
	return render_template("navbar.js")


@app.route("/js/jobs")
def jobs_js ():
	return render_template("jobs.js")
