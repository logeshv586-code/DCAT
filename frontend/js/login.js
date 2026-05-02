// Handles the login page functionality
(function () {
    var API = window.location.origin;

    // If user already has a token, just go straight to the dashboard
    if (localStorage.getItem("dcat_token")) {
        window.location.href = "dashboard.html";
        return;
    }

    var form = document.getElementById("loginForm");
    var errorDiv = document.getElementById("loginError");
    var btn = document.getElementById("loginBtn");

    form.addEventListener("submit", function (e) {
        e.preventDefault();
        errorDiv.style.display = "none"; // Hide any previous errors

        var username = document.getElementById("username").value.trim();
        var password = document.getElementById("password").value;

        if (!username || !password) {
            showError("Please fill in both username and password.");
            return;
        }

        // Show loading state on the button
        btn.querySelector(".btn-text").style.display = "none";
        btn.querySelector(".btn-loader").style.display = "inline-flex";
        btn.disabled = true;

        // Send login request to the API
        fetch(API + "/api/login", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ username: username, password: password }),
        })
            .then(function (res) {
                if (!res.ok) {
                    return res.json().then(function (data) {
                        throw new Error(data.detail || "Login failed");
                    });
                }
                return res.json();
            })
            .then(function (data) {
                // Save token and username to localStorage
                localStorage.setItem("dcat_token", data.token);
                localStorage.setItem("dcat_username", data.username);
                window.location.href = "dashboard.html";
            })
            .catch(function (err) {
                showError(err.message);
            })
            .finally(function () {
                // Reset the button state whether it succeeded or failed
                btn.querySelector(".btn-text").style.display = "inline";
                btn.querySelector(".btn-loader").style.display = "none";
                btn.disabled = false;
            });
    });

    // Helper function to show an error message
    function showError(msg) {
        errorDiv.textContent = msg;
        errorDiv.style.display = "block";
    }
})();

