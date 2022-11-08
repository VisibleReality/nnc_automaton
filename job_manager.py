from typing import Collection

from job import Job, JobStatus
from job_queue import JobQueue
from config import Config
from custom_exceptions import IdAlreadyUsedException


class JobManager:
	def __init__ (self):
		"""
		Create a new job manager, which should manage all the jobs for the application
		"""
		# Dict to store all the jobs
		self.jobs: dict[str, Job] = {}

		# Create a job queue to manage job rendering
		self._job_queue = JobQueue(Config.get("thread_count"))
		self._job_queue.start_threads()

	def add_job (self, new_job: Job) -> None:
		"""
		Add a new job to this job manager
		:param new_job: The job to be added
		:return: None
		"""
		if new_job.id not in self.jobs:
			self.jobs[new_job.id] = new_job
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
