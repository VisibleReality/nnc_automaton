function save (clicked) {
	fetch("{{ url_for('save') }}")
		.then(response => response.json())
		.then(response => {
			if (response === true) {
				let old_icon;
				clicked.children[0].classList.forEach((item) => {
					if (item.startsWith("bi-")) {
						old_icon = item;
					}
				});
				clicked.children[0].classList.replace(old_icon, "bi-check-circle");
				setTimeout( () => {
					clicked.children[0].classList.replace("bi-check-circle", old_icon);
				}, 5000);
			}
		});
}