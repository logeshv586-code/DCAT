// dashboard.js — main application logic for the creative generator
(function () {
    var API = window.location.origin;
    var TOKEN = localStorage.getItem("dcat_token");
    var USERNAME = localStorage.getItem("dcat_username");

    // redirect if not logged in
    if (!TOKEN) {
        window.location.href = "index.html";
        return;
    }

    // --- setup ---
    document.getElementById("userGreeting").textContent = "Hi, " + USERNAME;

    document.getElementById("logoutBtn").addEventListener("click", function () {
        localStorage.removeItem("dcat_token");
        localStorage.removeItem("dcat_username");
        window.location.href = "index.html";
    });

    // track state
    var selectedFile = null;
    var generatedResults = [];

    // --- references to DOM elements ---
    var accountSelect = document.getElementById("accountSelect");
    var dealerCard = document.getElementById("dealerCard");
    var dealerList = document.getElementById("dealerList");
    var selectAllDealers = document.getElementById("selectAllDealers");
    var assetCard = document.getElementById("assetCard");
    var logoToggle = document.getElementById("logoToggle");
    var logoOptions = document.getElementById("logoOptions");
    var uploadCard = document.getElementById("uploadCard");
    var dropZone = document.getElementById("dropZone");
    var bgFileInput = document.getElementById("bgFileInput");
    var bgPreviewWrap = document.getElementById("bgPreviewWrap");
    var bgPreview = document.getElementById("bgPreview");
    var removeBg = document.getElementById("removeBg");
    var formatCard = document.getElementById("formatCard");
    var generateCard = document.getElementById("generateCard");
    var generateBtn = document.getElementById("generateBtn");
    var progressWrap = document.getElementById("progressWrap");
    var progressFill = document.getElementById("progressFill");
    var progressText = document.getElementById("progressText");
    var resultsPanel = document.getElementById("resultsPanel");
    var resultsGrid = document.getElementById("resultsGrid");
    var downloadAllBtn = document.getElementById("downloadAllBtn");
    var previewModal = document.getElementById("previewModal");
    var modalImage = document.getElementById("modalImage");
    var modalDownload = document.getElementById("modalDownload");

    // helper for API calls
    function apiFetch(url, options) {
        options = options || {};
        options.headers = options.headers || {};
        options.headers["Authorization"] = "Bearer " + TOKEN;
        return fetch(API + url, options).then(function (res) {
            if (res.status === 401) {
                // token expired
                localStorage.removeItem("dcat_token");
                window.location.href = "index.html";
                return;
            }
            return res;
        });
    }

    function showCard(card) {
        card.style.display = "block";
        card.classList.add("visible");
    }

    // --- step 1: load accounts ---
    apiFetch("/api/accounts")
        .then(function (res) { return res.json(); })
        .then(function (accounts) {
            accounts.forEach(function (acct) {
                var opt = document.createElement("option");
                opt.value = acct.id;
                opt.textContent = acct.name;
                accountSelect.appendChild(opt);
            });
        });

    // when brand changes, load its dealers
    accountSelect.addEventListener("change", function () {
        var accountId = accountSelect.value;
        dealerList.innerHTML = "";
        selectAllDealers.checked = false;

        if (!accountId) {
            dealerCard.style.display = "none";
            assetCard.style.display = "none";
            uploadCard.style.display = "none";
            formatCard.style.display = "none";
            generateCard.style.display = "none";
            return;
        }

        apiFetch("/api/accounts/" + accountId + "/dealers")
            .then(function (res) { return res.json(); })
            .then(function (dealers) {
                dealers.forEach(function (d) {
                    var label = document.createElement("label");
                    label.className = "checkbox-row";
                    label.innerHTML =
                        '<input type="checkbox" class="dealer-cb" value="' + d.id + '">' +
                        "<span>" + d.name + "</span>";
                    dealerList.appendChild(label);
                });

                showCard(dealerCard);
                showCard(assetCard);
                showCard(uploadCard);
                showCard(formatCard);
                showCard(generateCard);
                updateGenerateBtn();
            });
    });

    // select all checkbox
    selectAllDealers.addEventListener("change", function () {
        var checked = selectAllDealers.checked;
        var cbs = dealerList.querySelectorAll(".dealer-cb");
        cbs.forEach(function (cb) { cb.checked = checked; });
        updateGenerateBtn();
    });

    // individual dealer checkboxes
    dealerList.addEventListener("change", function (e) {
        if (e.target.classList.contains("dealer-cb")) {
            var all = dealerList.querySelectorAll(".dealer-cb");
            var allChecked = Array.from(all).every(function (cb) { return cb.checked; });
            selectAllDealers.checked = allChecked;
            updateGenerateBtn();
        }
    });

    // --- step 3: logo toggle ---
    logoToggle.addEventListener("change", function () {
        logoOptions.style.display = logoToggle.checked ? "flex" : "none";
    });

    // --- step 4: background upload ---
    dropZone.addEventListener("click", function () {
        bgFileInput.click();
    });

    dropZone.addEventListener("dragover", function (e) {
        e.preventDefault();
        dropZone.classList.add("dragover");
    });

    dropZone.addEventListener("dragleave", function () {
        dropZone.classList.remove("dragover");
    });

    dropZone.addEventListener("drop", function (e) {
        e.preventDefault();
        dropZone.classList.remove("dragover");
        var files = e.dataTransfer.files;
        if (files.length > 0) {
            handleFileSelect(files[0]);
        }
    });

    bgFileInput.addEventListener("change", function () {
        if (bgFileInput.files.length > 0) {
            handleFileSelect(bgFileInput.files[0]);
        }
    });

    function handleFileSelect(file) {
        var ext = file.name.split(".").pop().toLowerCase();
        if (["jpg", "jpeg", "png"].indexOf(ext) === -1) {
            alert("Please upload a JPG or PNG image.");
            return;
        }

        selectedFile = file;
        var reader = new FileReader();
        reader.onload = function (e) {
            bgPreview.src = e.target.result;
            bgPreviewWrap.style.display = "block";
            dropZone.style.display = "none";
        };
        reader.readAsDataURL(file);
        updateGenerateBtn();
    }

    removeBg.addEventListener("click", function () {
        selectedFile = null;
        bgPreview.src = "";
        bgPreviewWrap.style.display = "none";
        dropZone.style.display = "block";
        bgFileInput.value = "";
        updateGenerateBtn();
    });

    // --- step 6: generate ---
    function getSelectedDealerIds() {
        var cbs = dealerList.querySelectorAll(".dealer-cb:checked");
        return Array.from(cbs).map(function (cb) { return cb.value; });
    }

    function updateGenerateBtn() {
        var ids = getSelectedDealerIds();
        generateBtn.disabled = !(ids.length > 0 && selectedFile);
    }

    generateBtn.addEventListener("click", function () {
        var ids = getSelectedDealerIds();
        if (ids.length === 0 || !selectedFile) return;

        var fmt = document.querySelector('input[name="outputFormat"]:checked').value;
        var logoVal = "off";
        if (logoToggle.checked) {
            logoVal = document.querySelector('input[name="logoVariant"]:checked').value;
        }

        // build form data
        var formData = new FormData();
        formData.append("background", selectedFile);
        formData.append("dealer_ids", ids.join(","));
        formData.append("output_format", fmt);
        formData.append("logo_enabled", logoVal);

        // UI: show progress
        generateBtn.querySelector(".btn-text").style.display = "none";
        generateBtn.querySelector(".btn-loader").style.display = "inline-flex";
        generateBtn.disabled = true;
        progressWrap.style.display = "block";
        progressFill.style.width = "30%";
        progressText.textContent = "Generating " + ids.length + " creative(s)...";

        apiFetch("/api/generate", {
            method: "POST",
            body: formData,
        })
            .then(function (res) {
                progressFill.style.width = "80%";
                return res.json();
            })
            .then(function (data) {
                progressFill.style.width = "100%";
                progressText.textContent = "Done! " + data.count + " creative(s) generated.";

                generatedResults = data.results || [];
                renderResults();

                // reset progress after a moment
                setTimeout(function () {
                    progressWrap.style.display = "none";
                    progressFill.style.width = "0%";
                }, 2000);
            })
            .catch(function (err) {
                progressText.textContent = "Error: " + err.message;
                progressFill.style.width = "0%";
            })
            .finally(function () {
                generateBtn.querySelector(".btn-text").style.display = "inline";
                generateBtn.querySelector(".btn-loader").style.display = "none";
                generateBtn.disabled = false;
                updateGenerateBtn();
            });
    });

    // --- step 7: results ---
    function renderResults() {
        resultsGrid.innerHTML = "";

        if (generatedResults.length === 0) {
            resultsPanel.style.display = "none";
            return;
        }

        resultsPanel.style.display = "block";

        generatedResults.forEach(function (r) {
            if (r.error) {
                var errDiv = document.createElement("div");
                errDiv.className = "result-error";
                errDiv.textContent = r.dealer_name + ": " + r.error;
                resultsGrid.appendChild(errDiv);
                return;
            }

            var card = document.createElement("div");
            card.className = "result-card";

            var imgUrl = API + "/output/" + r.output_filename;

            card.innerHTML =
                '<img src="' + imgUrl + '" alt="' + r.dealer_name + '">' +
                '<div class="result-card-info">' +
                "<span>" + r.dealer_name + "</span>" +
                '<a href="' + API + "/api/download/" + r.output_filename + '" download>Download</a>' +
                "</div>";

            // click image to preview
            card.querySelector("img").addEventListener("click", function () {
                openPreview(imgUrl, r.output_filename);
            });

            // stop download link from triggering the preview
            card.querySelector("a").addEventListener("click", function (e) {
                e.stopPropagation();
            });

            resultsGrid.appendChild(card);
        });
    }

    // preview modal
    function openPreview(imgUrl, filename) {
        modalImage.src = imgUrl;
        modalDownload.href = API + "/api/download/" + filename;
        modalDownload.setAttribute("download", filename);
        previewModal.style.display = "flex";
    }

    document.getElementById("closeModal").addEventListener("click", function () {
        previewModal.style.display = "none";
    });

    document.querySelector(".modal-backdrop").addEventListener("click", function () {
        previewModal.style.display = "none";
    });

    // download all as ZIP
    downloadAllBtn.addEventListener("click", function () {
        var filenames = generatedResults
            .filter(function (r) { return !r.error; })
            .map(function (r) { return r.output_filename; });

        if (filenames.length === 0) return;

        apiFetch("/api/download-zip", {
            method: "POST",
            headers: {
                "Content-Type": "application/json",
                "Authorization": "Bearer " + TOKEN,
            },
            body: JSON.stringify(filenames),
        })
            .then(function (res) { return res.blob(); })
            .then(function (blob) {
                // trigger download
                var url = URL.createObjectURL(blob);
                var a = document.createElement("a");
                a.href = url;
                a.download = "creatives.zip";
                document.body.appendChild(a);
                a.click();
                document.body.removeChild(a);
                URL.revokeObjectURL(url);
            })
            .catch(function (err) {
                alert("Failed to download ZIP: " + err.message);
            });
    });

    // listen for format changes (update button state)
    document.querySelectorAll('input[name="outputFormat"]').forEach(function (r) {
        r.addEventListener("change", updateGenerateBtn);
    });
})();
