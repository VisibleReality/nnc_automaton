function save (clicked) {
	fetch("/save")
		.then(response => response.json())
		.then(response => {
			if (response === true) {
				clicked.children["save-icon"].classList.remove("bi-save");
				clicked.children["save-icon"].classList.add("bi-check-circle");
			}
		});
}