import atexit
import pathlib
from typing import NamedTuple

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

		# Load state from disk, if it exists
		if load_state and pathlib.Path(Config.get("savestate_file")).exists():
			with open(Config.get("savestate_file"), "r") as save_file:
				save_state: JobManagerSave = jsonpickle.decode(save_file.read())

			# Dict to store all the jobs
			self.jobs: dict[str, Job] = save_state.jobs

			# Create a job queue
			self._job_queue = JobQueue(Config.get("thread_count"))

			# Search for in-progress jobs and add to the start of the queue
			for job in self.jobs.values():
				if job.status in (JobStatus.AudioProcessing, JobStatus.VideoProcessing):
					job.status = JobStatus.Waiting
					self.queue_job(job.id)

			# Queue the remaining jobs
			for job_id in save_state.queue:
				self.jobs[job_id].status = JobStatus.Waiting
				self.queue_job(job_id)

		# self._job_queue.start_threads() TODO uncomment
		# Load a blank state
		else:
			# Dict to store all the jobs
			self.jobs: dict[str, Job] = {}
			# Create a job queue to manage job rendering
			self._job_queue = JobQueue(Config.get("thread_count"))
		# self._job_queue.start_threads()

		atexit.register(self._exit_handler)

	def _exit_handler (self):
		# When using the debug server don't autosave state
		# self.save_state()
		pass

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
			self.dequeue_job(job_id)
			del self.jobs[job_id]
			return True
		else:
			return False

	def dequeue_job (self, job_id: str) -> bool:
		"""
		Remove a job from the queue
		:param job_id: The id of the job to dequeue
		:return: True if the job was in the queue, false otherwise
		"""
		if job_id in self._job_queue.get_queue_ids():
			self._job_queue.delete_job(self.jobs[job_id])
			self.jobs[job_id].status = JobStatus.Waiting
			return True
		else:
			return False

	def get_jobs_with_status (self, *statuses: JobStatus) -> dict[str, Job]:
		"""
		Get all jobs with given status
		:param statuses: One or more job statuses to get jobs with. If no statues are specified, returns all jobs
		:return: A dictionary containing only the jobs with the given statuses
		"""
		if len(statuses) != 0:
			return {job_id: job for job_id, job in self.jobs.items() if job.status in statuses}
		else:
			return self.jobs

	def get_queue (self) -> list[Job]:
		"""
		Gets all jobs in the queue, including the ones currently in progress (at the start)
		This is a copy of the queue, modifying it will not modify the queue
		:return: A list of all jobs in the queue
		"""
		in_progress = [job for job in self.jobs.values() if job.status in
					   (JobStatus.AudioProcessing, JobStatus.VideoProcessing)]
		return in_progress + [self.jobs[job_id] for job_id in self._job_queue.get_queue_ids()]

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
		print(f"Saved state to {Config.get('savestate_file')}")

	def get_counts (self) -> dict[str, int]:
		"""
		Return a dictionary containing counts of each type of job. The categories are
		:return:
		"""
		return {"total":      len(self.jobs),
				"waiting":    len(self.get_jobs_with_status(JobStatus.Waiting)),
				"queued":     len(self.get_jobs_with_status(JobStatus.Queued)),
				"processing": len(self.get_jobs_with_status(JobStatus.AudioProcessing,
															JobStatus.VideoProcessing)),
				"done":       len(self.get_jobs_with_status(JobStatus.Done)),
				"uploaded":   len(self.get_jobs_with_status(JobStatus.Uploaded)),
				"failed":     len(self.get_jobs_with_status(JobStatus.Failed, JobStatus.Deleted))}


class JobManagerSave(NamedTuple):
	jobs: dict[str, Job]
	queue: list[str]
