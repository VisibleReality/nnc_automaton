function show_checkmark_icon (element) {
	if (!element.classList.contains("bi-check-circle")) {
		let old_icon;
		element.classList.forEach((item) => {
			if (item.startsWith("bi-")) {
				old_icon = item;
			}
		});
		element.classList.replace(old_icon, "bi-check-circle");
		setTimeout(() => {
			element.classList.replace("bi-check-circle", old_icon);
		}, 5000);
	}
}

function fetch_then_if_true (url, func, args) {
	fetch(url)
		.then(response => response.json())
		.then(response => {
			if (response === true) {
				func(...args)
			}
		})
}


function job_queue (clicked, job_id) {
	fetch_then_if_true("{{ url_for('queue_job', job_id = 'JOB_ID') }}".replace("JOB_ID", job_id),
		show_checkmark_icon, [clicked.children[0]]);
}

function job_queue_all (clicked) {
	fetch_then_if_true("{{ url_for('queue_all_ready') }}",
		show_checkmark_icon, [clicked.children[0]]);
}

function job_dequeue (clicked, job_id) {
	fetch_then_if_true("{{ url_for('dequeue_job', job_id = 'JOB_ID') }}".replace("JOB_ID", job_id),
		show_checkmark_icon, [clicked.children[0]]);
}

function job_delete (clicked, job_id) {
	fetch_then_if_true("{{ url_for('delete_job', job_id = 'JOB_ID') }}".replace("JOB_ID", job_id),
		show_checkmark_icon, [clicked.children[0]]);
}

function job_set_youtube_info (clicked, job_id) {
	fetch_then_if_true("{{ url_for('set_youtube_info', job_id = 'JOB_ID') }}".replace("JOB_ID", job_id),
		show_checkmark_icon, [clicked.children[0]]);
}

function job_set_youtube_info_all (clicked, job_id) {
	fetch_then_if_true("{{ url_for('set_youtube_info_all') }}",
		show_checkmark_icon, [clicked.children[0]]);
}

function update_image(source, image_id) {
	var selectedFile = source.files[0];
	console.log(selectedFile)
	var img = document.getElementById(image_id);

	var reader = new FileReader();
	reader.onload = (e) => {
		console.log(e.target.result)
		img.src = e.target.result;
	}

	reader.readAsDataURL(selectedFile)
}

const forms = document.querySelectorAll('.needs-validation');

Array.from(forms).forEach(form => {
	form.addEventListener('submit', event => {
		if (!form.checkValidity()) {
			event.preventDefault();
			event.stopPropagation();
		}

		form.classList.add("was-validated");
	}, false);
});