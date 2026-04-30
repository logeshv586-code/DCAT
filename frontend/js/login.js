// login.js — handles the login form
(function () {
    var API = window.location.origin;

    // if already logged in, go straight to dashboard
    if (localStorage.getItem("dcat_token")) {
        window.location.href = "dashboard.html";
        return;
    }

    var form = document.getElementById("loginForm");
    var errorDiv = document.getElementById("loginError");
    var btn = document.getElementById("loginBtn");

    form.addEventListener("submit", function (e) {
        e.preventDefault();
        errorDiv.style.display = "none";

        var username = document.getElementById("username").value.trim();
        var password = document.getElementById("password").value;

        if (!username || !password) {
            showError("Please fill in both fields.");
            return;
        }

        // show loading state
        btn.querySelector(".btn-text").style.display = "none";
        btn.querySelector(".btn-loader").style.display = "inline-flex";
        btn.disabled = true;

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
                localStorage.setItem("dcat_token", data.token);
                localStorage.setItem("dcat_username", data.username);
                window.location.href = "dashboard.html";
            })
            .catch(function (err) {
                showError(err.message);
            })
            .finally(function () {
                btn.querySelector(".btn-text").style.display = "inline";
                btn.querySelector(".btn-loader").style.display = "none";
                btn.disabled = false;
            });
    });

    function showError(msg) {
        errorDiv.textContent = msg;
        errorDiv.style.display = "block";
    }
})();
