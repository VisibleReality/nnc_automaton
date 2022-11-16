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
def save_timer ():
	time.sleep(1800)
	job_manager.save_state()


threading.Thread(target = save_timer, daemon = True)


# -- MISC --

@app.route("/")
def main_page ():
	job_counts = {"total":      len(job_manager.jobs),
				  "waiting":    len(job_manager.get_jobs_with_status(JobStatus.Waiting)),
				  "queued":     len(job_manager.get_jobs_with_status(JobStatus.Queued)),
				  "processing": len(job_manager.get_jobs_with_status(JobStatus.AudioProcessing,
																	 JobStatus.VideoProcessing)),
				  "done":       len(job_manager.get_jobs_with_status(JobStatus.Done)),
				  "failed":     len(job_manager.get_jobs_with_status(JobStatus.Failed))}

	return render_template("index.html", job_counts = job_counts)


@app.route("/settings")
def settings ():
	return "Settings"


@app.route("/favicon.ico")
def favicon ():
	return send_file("./nightnightcore.ico")


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
			elif job_type == "failed":
				job_statues.append(JobStatus.Failed)
			elif job_type == "deleted":
				job_statues.append(JobStatus.Deleted)

	job_counts = {"total":      len(job_manager.jobs),
				  "waiting":    len(job_manager.get_jobs_with_status(JobStatus.Waiting)),
				  "queued":     len(job_manager.get_jobs_with_status(JobStatus.Queued)),
				  "processing": len(job_manager.get_jobs_with_status(JobStatus.AudioProcessing,
																	 JobStatus.VideoProcessing)),
				  "done":       len(job_manager.get_jobs_with_status(JobStatus.Done)),
				  "failed":     len(job_manager.get_jobs_with_status(JobStatus.Failed)),
				  "deleted":    len(job_manager.get_jobs_with_status(JobStatus.Deleted))}

	jobs = job_manager.get_jobs_with_status(*job_statues)

	return render_template("jobs.html", request_terms = request_terms, job_counts = job_counts, jobs = jobs)


@app.route("/job/<job_id>")
def job_page (job_id: str):
	job = job_manager.jobs[job_id]
	return jsonpickle.encode(job)


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
