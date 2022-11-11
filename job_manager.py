import atexit
from typing import Collection, NamedTuple

import jsonpickle

from job import Job, JobStatus
from job_queue import JobQueue
from config import Config
from custom_exceptions import IdAlreadyUsedException


class JobManager:
	def __init__ (self, load_state: bool = False):
		"""
		Create a new job manager, which should manage all the jobs for the application
		:param load_state: Set to true to load state from disk
		"""

		# Load state from disk
		if load_state:
			with open(Config.get("savestate_file"), "r") as save_file:
				save_state: JobManagerSave = jsonpickle.decode(save_file.read())

			# Dict to store all the jobs
			self.jobs: dict[str, Job] = save_state.jobs

			# Search for in-progress jobs and add to the start of the queue
			for job in self.jobs.values():
				if job.status in (JobStatus.AudioProcessing, JobStatus.VideoProcessing):
					save_state.queue.insert(0, job.id)

			# Create a job queue with preset jobs
			self._job_queue = JobQueue(Config.get("thread_count"), [self.jobs[job_id] for job_id in save_state.queue])
			self._job_queue.start_threads()
		# Load a blank state
		else:
			# Dict to store all the jobs
			self.jobs: dict[str, Job] = {}
			# Create a job queue to manage job rendering
			self._job_queue = JobQueue(Config.get("thread_count"))
			self._job_queue.start_threads()

		atexit.register(self._exit_handler)

	def _exit_handler (self):
		self.save_state()

	def add_job (self, new_job: Job) -> str:
		"""
		Add a new job to this job manager
		:param new_job: The job to be added
		:return: The id of the job that was added
		"""
		if new_job.id not in self.jobs:
			self.jobs[new_job.id] = new_job
			return new_job.id
		else:
			raise IdAlreadyUsedException(f"Job ID {new_job.id} already used")

	def delete_job (self, job_id: str) -> bool:
		"""
		Delete a job and its files
		:param job_id: The job id to delete
		:return: True if the job existed, false otherwise
		"""
		if job_id in self.jobs:
			self.jobs[job_id].cleanup_files()
			del self.jobs[job_id]
			return True
		else:
			return False

	def get_jobs_with_status (self, statuses: Collection[JobStatus]) -> dict[str, Job]:
		"""
		Get all jobs with given status
		:param statuses: Collection of statuses to return jobs with
		:return: A dictionary containing only the jobs with the given statuses
		"""
		return {job_id: job for job_id, job in self.jobs.items() if job.status in statuses}

	def queue_job (self, job_id: str) -> bool:
		"""
		Queue a job given its id
		:param job_id: The id of the job to queue
		:return: True if the job was queued, false otherwise
		"""
		if job_id in self.jobs:
			return self._job_queue.queue_job(self.jobs[job_id])
		else:
			return False

	def queue_all_ready_waiting (self) -> int:
		"""
		Add all jobs which are both ready, and have a status of waiting, to the queue
		:return: The amount of jobs queued
		"""
		count = 0
		for job_id, job in self.jobs.items():
			if job.status == JobStatus.Waiting and job.check_ready():
				if self._job_queue.queue_job(job):
					count += 1
		return count

	def save_state (self) -> None:
		"""
		Save the current state of this job manager to a file. The location of the file is defined by the config file
		:return:
		"""
		save_state = JobManagerSave(jobs = self.jobs, queue = self._job_queue.get_queue_ids())
		with open(Config.get("savestate_file"), "w") as save_file:
			save_file.write(jsonpickle.encode(save_state))


class JobManagerSave(NamedTuple):
	jobs: dict[str, Job]
	queue: list[str]
