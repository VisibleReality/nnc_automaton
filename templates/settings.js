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

const googleLoginButton = document.getElementById("google-login");

if (window.location.host !== "localhost:8080")
{
	googleLoginButton.classList.add("disabled");
}