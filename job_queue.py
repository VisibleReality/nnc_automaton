import queue
import threading
from collections import deque
from collections.abc import Collection

from job import JobStatus, Job


class JobQueue:
	def __init__ (self, thread_count: int = 1, starting_queue: Collection[Job] = None):
		"""
		Creates a new job queue, which manages the execution of jobs
		:param thread_count: The amount of threads to create (default 1)
		:param starting_queue: A collection of items to insert into the queue
		"""
		self._queue: queue.Queue[Job] = queue.Queue()

		if starting_queue is not None:
			for job in starting_queue:
				self._queue.put(job)

		# Initialise the given amount of threads
		self._threads = [threading.Thread(target = self._thread_worker, args = [x], daemon = True)
						 for x in range(thread_count)]

	def _thread_worker (self, thread_number: int) -> None:
		print(f"Thread {thread_number} started")
		while True:
			# Get next available job
			current_job = self._queue.get()
			print(f"Thread {thread_number}: got job {current_job.id} ({current_job.song_title})")

			# Skip jobs that cause exceptions, and note what the exception is
			try:
				current_job.run_job()
				print(f"Thread {thread_number}: Job {current_job.id} ({current_job.song_title}) succeeded")
			except Exception as exception:
				print(f"Thread {thread_number}: Job {current_job.id} ({current_job.song_title}) failed")
				current_job.status = JobStatus.Failed
				current_job.failure_info = str(exception)

			# Mark job as done
			self._queue.task_done()
			print(f"Thread {thread_number}: Job {current_job.id} ({current_job.song_title}) done")

	def start_threads (self) -> None:
		"""
		Start processing jobs
		:return: None
		"""
		for thread in self._threads:
			thread.start()

	def get_queue_ids (self) -> list[str]:
		"""
		Get the current state of the queue
		:return: A list containing the ids of all jobs in the queue, from first to last
		(not including currently processing jobs)
		"""
		return [job.id for job in self._queue.queue]

	def queue_job (self, new_job: Job) -> bool:
		"""
		Add a job to the queue
		:param new_job: The job to be added, must be ready, and waiting or failed
		:return: True if the job was successfully added to the queue, false otherwise
		"""
		# Only allow queueing jobs which are ready
		if new_job.status in (JobStatus.Waiting, JobStatus.Failed) and new_job.check_ready():
			new_job.status = JobStatus.Queued
			new_job.failure_info = None
			self._queue.put(new_job)
			return True
		else:
			return False

	def delete_job (self, job: Job) -> None:
		"""
		Remove a job from the queue
		:param job: The job to remove
		:return: None
		"""
		self._queue.queue.remove(job)
