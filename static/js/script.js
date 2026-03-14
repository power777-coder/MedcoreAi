function getCSRFToken() {
    return document.getElementById("csrfToken").value;
}

// Check for saved errors from previous redirect
window.addEventListener("load", function() {
    const savedError = localStorage.getItem("googleLoginError");
    if(savedError) {
        console.log("📋 SAVED ERROR FROM PREVIOUS CLICK:", savedError);
        console.log("localStorage value:", savedError);
        // Clear it
        localStorage.removeItem("googleLoginError");
    }
});


/* ===============================
   PAGE NAVIGATION
================================ */

function showPage(pageId){

    document.querySelectorAll('.content-overlay')
        .forEach(p => p.classList.add('hidden'));

    document.getElementById(pageId).classList.remove('hidden');

    /* Reset login */
    if(pageId === 'page2'){
        document.getElementById('userNameInput').value = "";
        document.getElementById('userEmailInput').value = "";
        document.getElementById('pass').value = "";
    }

    /* Dashboard */
    if(pageId === "page3"){

        const historyPanel = document.getElementById("historyPanel");
        if(historyPanel){
            historyPanel.style.display = "none";
            historyPanel.innerHTML = "";
        }

        loadUserProfile();
    }

    /* Analyzer */
    if(pageId === "page4"){
        loadSymptoms();
        selectedSymptoms.clear();

        const searchBox = document.getElementById("symptomSearch");
        if(searchBox) searchBox.value = "";

        const chatbotInput = document.getElementById("chatbotInput");
        if(chatbotInput) chatbotInput.value = "";

        resetAdvisorInputs();

        renderSymptoms(allSymptoms);
    }
}

function attachGoogleButtonListener() {
    const googleBtn = document.getElementById("googleLoginBtn");
    if(!googleBtn) {
        console.warn("Google login button not found");
        return;
    }

    if(googleBtn.dataset.listenerAttached === "true") {
        return;
    }

    googleBtn.dataset.listenerAttached = "true";
    googleBtn.addEventListener("click", function(e) {
        e.preventDefault();
        googleLogin();
    });
}


/* ===============================
   USER PROFILE
================================ */

function loadUserProfile(){

    fetch("/accounts/user-info/")
    .then(res => res.json())
    .then(data => {

        const name = data.name && data.name.trim() !== ""
            ? data.name
            : data.email;

        document.getElementById("displayName").innerText =
            data.name || data.email;

        document.getElementById("displayEmail").innerText =
            data.email;

        document.getElementById("userAvatar").src =
            `https://ui-avatars.com/api/?name=${encodeURIComponent(name)}&background=00d2ff&color=fff&size=256`;

        const patientName = document.getElementById("doctorPatientName");
        const contactEmail = document.getElementById("doctorContactEmail");
        if(patientName && !patientName.value) patientName.value = data.name || data.email;
        if(contactEmail && !contactEmail.value) contactEmail.value = data.email;

        loadDoctorPlans();

    })
    .catch(()=>{
        document.getElementById("displayName").innerText = "User";
    });
}

function loadDoctorPlans(){

    fetch("/accounts/doctor/plans/")
    .then(async res => {
        const data = await res.json();
        if(!res.ok){
            throw new Error(data.message || "Unable to load doctor plans.");
        }
        return data;
    })
    .then(data => {
        renderDoctorPlans(data.plans || [], data.active_purchase, data.google_meet_enabled);
        renderDoctorConsultations(data.consultations || []);
    })
    .catch(error => {
        const statusCard = document.getElementById("doctorPlanStatus");
        if(statusCard){
            statusCard.innerText = error.message || "Unable to load doctor plans.";
        }
    });
}

function renderDoctorPlans(plans, activePurchase, googleMeetEnabled){

    const statusCard = document.getElementById("doctorPlanStatus");
    const list = document.getElementById("doctorPlanList");
    if(!statusCard || !list) return;

    if(activePurchase){
        statusCard.innerHTML = `
            <strong>${activePurchase.plan_name}</strong><br>
            Payment: ${activePurchase.payment_status}<br>
            Remaining doctor sessions: ${activePurchase.remaining_sessions}<br>
            Reference: ${activePurchase.payment_reference}
        `;
    } else {
        statusCard.innerHTML = `
            <strong>No active doctor plan</strong><br>
            Buy a premium plan to unlock doctor contact and paid consultations.
        `;
    }

    list.innerHTML = "";

    plans.forEach(plan => {
        const card = document.createElement("div");
        card.className = "doctor-plan-card";
        card.innerHTML = `
            <div>
                <h3>${plan.name}</h3>
                <p>${plan.description}</p>
                <span>${plan.sessions_included} consultation${plan.sessions_included > 1 ? "s" : ""}</span>
            </div>
            <div class="doctor-plan-footer">
                <strong>Rs. ${plan.price_inr}</strong>
                <button class="btn-primary-glow doctor-plan-btn" onclick="activateDoctorPlan('${plan.code}')">
                    Pay & Activate
                </button>
            </div>
        `;
        list.appendChild(card);
    });

    const mode = document.getElementById("doctorConsultMode");
    if(mode && !googleMeetEnabled && mode.value === "google_meet"){
        mode.value = "video_call";
    }
}

function renderDoctorConsultations(consultations){

    const container = document.getElementById("doctorConsultationList");
    if(!container) return;

    if(!consultations.length){
        container.innerHTML = '<p class="doctor-empty-state">No doctor consultations booked yet.</p>';
        return;
    }

    container.innerHTML = consultations.map(item => `
        <div class="doctor-consultation-card">
            <div class="doctor-consultation-top">
                <strong>${item.patient_name}</strong>
                <span>${item.status}</span>
            </div>
            <p>${item.symptoms_summary}</p>
            <small>${item.consultation_mode} | Preferred: ${item.preferred_date || "Not specified"} | Requested: ${item.created_at}</small>
            ${item.meeting_link ? `<a href="${item.meeting_link}" target="_blank" rel="noopener noreferrer" class="doctor-meet-link">Join consultation</a>` : ""}
        </div>
    `).join("");
}

function activateDoctorPlan(planCode){

    fetch("/accounts/doctor/activate/", {
        method: "POST",
        headers: {
            "Content-Type": "application/json",
            "X-CSRFToken": getCSRFToken()
        },
        body: JSON.stringify({ plan_code: planCode })
    })
    .then(async res => {
        const data = await res.json();
        if(!res.ok){
            throw new Error(data.message || "Plan activation failed.");
        }
        return data;
    })
    .then(data => {
        showDoctorBookingMessage({
            type: "info",
            title: "Plan activated",
            body: `${data.message} Now choose Google Meet With Doctor or Video Call With Doctor below.`,
        });
        loadDoctorPlans();
        const mode = document.getElementById("doctorConsultMode");
        if(mode){
            mode.focus();
        }
    })
    .catch(error => {
        showDoctorBookingMessage({
            type: "error",
            title: "Plan activation failed",
            body: error.message || "Plan activation failed.",
        });
    });
}

function bookDoctorConsultation(event){

    event.preventDefault();

    const payload = {
        patient_name: document.getElementById("doctorPatientName").value.trim(),
        contact_email: document.getElementById("doctorContactEmail").value.trim(),
        preferred_date: document.getElementById("doctorPreferredDate").value,
        consultation_mode: document.getElementById("doctorConsultMode").value,
        symptoms_summary: document.getElementById("doctorSymptomsSummary").value.trim()
    };

    fetch("/accounts/doctor/book/", {
        method: "POST",
        headers: {
            "Content-Type": "application/json",
            "X-CSRFToken": getCSRFToken()
        },
        body: JSON.stringify(payload)
    })
    .then(async res => {
        const data = await res.json();
        if(!res.ok){
            throw new Error(data.message || "Doctor consultation booking failed.");
        }
        return data;
    })
    .then(data => {
        const consultation = data.consultation || {};

        showDoctorBookingMessage({
            type: "success",
            title: "Doctor consultation booked successfully",
            body: consultation.meeting_link
                ? "Your consultation is confirmed. Use the link below to join or copy it."
                : "Your request is saved. Add DEFAULT_DOCTOR_MEET_LINK in .env to auto-share a Meet link.",
            link: consultation.meeting_link || "",
        });

        document.getElementById("doctorSymptomsSummary").value = "";
        loadDoctorPlans();
    })
    .catch(error => {
        showDoctorBookingMessage({
            type: "error",
            title: "Doctor consultation booking failed",
            body: error.message || "Doctor consultation booking failed.",
        });
    });
}

function openDoctorConnectFromResult(){
    if(!doctorConnectUnlocked){
        return;
    }

    const modal = document.getElementById("doctorConnectModal");
    if(modal){
        modal.classList.remove("hidden");
    }
    loadDoctorPlans();
}

function closeDoctorConnectModal(){
    const modal = document.getElementById("doctorConnectModal");
    if(modal){
        modal.classList.add("hidden");
    }
    hideDoctorBookingMessage();
}

function showDoctorBookingMessage({ type = "info", title = "", body = "", link = "" }){
    const container = document.getElementById("doctorBookingMessage");
    if(!container) return;

    const safeTitle = title || "";
    const safeBody = body || "";
    const safeLink = link || "";

    container.className = `doctor-booking-message doctor-booking-message-${type}`;
    container.innerHTML = `
        <div class="doctor-booking-message-top">
            <strong>${safeTitle}</strong>
            <button type="button" class="btn-back doctor-message-close" onclick="hideDoctorBookingMessage()">Close</button>
        </div>
        <p>${safeBody}</p>
        ${safeLink ? `
            <div class="doctor-booking-link-row">
                <input type="text" id="doctorMeetingLinkField" class="doctor-link-input" value="${safeLink}" readonly>
                <button type="button" class="btn-primary-glow doctor-copy-btn" onclick="copyDoctorMeetingLink()">Copy Link</button>
            </div>
            <a href="${safeLink}" target="_blank" rel="noopener noreferrer" class="doctor-meet-link">Open Google Meet</a>
        ` : ""}
    `;
}

function hideDoctorBookingMessage(){
    const container = document.getElementById("doctorBookingMessage");
    if(!container) return;

    container.className = "doctor-booking-message hidden";
    container.innerHTML = "";
}

function copyDoctorMeetingLink(){
    const input = document.getElementById("doctorMeetingLinkField");
    if(!input) return;

    input.select();
    input.setSelectionRange(0, 99999);
    navigator.clipboard.writeText(input.value)
        .then(() => {
            showDoctorBookingMessage({
                type: "success",
                title: "Link copied",
                body: "The Google Meet link has been copied. You can paste it anywhere.",
                link: input.value,
            });
        })
        .catch(() => {
            document.execCommand("copy");
        });
}


/* ===============================
   SIGN IN (SEND OTP)
================================ */

function handleSignIn(e){

    e.preventDefault();

    const name = document.getElementById("userNameInput").value;
    const email = document.getElementById("userEmailInput").value;
    const password = document.getElementById("pass").value;

    // First try login
    fetch("/accounts/login-user/",{
        method:"POST",
        headers:{
            "Content-Type":"application/json",
            "X-CSRFToken": getCSRFToken()
        },
        body: JSON.stringify({ email, password })
    })
    .then(res=>res.json())
    .then(data=>{

        if(data.success){

            console.log("Login success");

            showPage("page3");

        }

        else{

            // If login fails, try signup with OTP
            fetch("/accounts/send-otp/",{
                method:"POST",
                headers:{
                    "Content-Type":"application/json",
                    "X-CSRFToken": getCSRFToken()
                },
                body: JSON.stringify({ name,email,password })
            })
            .then(res=>res.json())
            .then(data=>{

                if(data.success){

                    showOTPModal();

                }
                else{

                    alert(data.message);

                }

            });

        }

    });

}


/* ===============================
   OTP FUNCTIONS
================================ */

function showOTPModal(){
    document.getElementById("otpModal").classList.remove("hidden");
    startOTPTimer();
}

function verifyOTP(){

    fetch("/accounts/verify-otp/",{
        method:"POST",
        headers:{
            "Content-Type":"application/json",
            "X-CSRFToken": getCSRFToken()
        },
        body: JSON.stringify({ otp:getOTP() })
    })
    .then(res=>res.json())
    .then(data=>{

        if(data.success){
            document.getElementById("otpModal").classList.add("hidden");
            showPage("page3");
        }
        else{
            alert(data.message || "Invalid OTP");
        }

    });
}

function resendOTP(){

    fetch("/accounts/send-otp/",{
        method:"POST",
        headers:{
            "Content-Type":"application/json",
            "X-CSRFToken": getCSRFToken()
        },
        body: JSON.stringify({
            name: document.getElementById("userNameInput").value,
            email: document.getElementById("userEmailInput").value,
            password: document.getElementById("pass").value
        })
    });

    document.getElementById("resendBtn").disabled = true;
    startOTPTimer();
}



function getOTP(){
    let otp="";
    document.querySelectorAll(".otp-digit")
        .forEach(i => otp += i.value);
    return otp;
}


/* OTP Timer */

let otpTime = 60;
let otpInterval;

function startOTPTimer(){

    clearInterval(otpInterval);

    otpTime = 60;

    otpInterval = setInterval(()=>{

        otpTime--;

        document.getElementById("otpTimer").innerText =
            `Resend OTP in ${otpTime}s`;

        if(otpTime <= 0){
            clearInterval(otpInterval);
            document.getElementById("resendBtn").disabled = false;
            document.getElementById("otpTimer").innerText = "";
        }

    },1000);
}


/* OTP Auto Focus + Auto Login Check */
document.addEventListener("DOMContentLoaded", async () => {
    try {

        const res = await fetch("/accounts/user-info/");

        if(res.ok){

            const data = await res.json();

            console.log("User already logged in:", data);

            showPage("page3");   // Go directly to dashboard
            loadUserProfile();

            return;

        }

    } catch(e){
        console.log("User not logged in");
    }

    // If not logged in
    showPage("page2");

});



/* ===============================
   SYMPTOMS
================================ */

let allSymptoms = [];
let selectedSymptoms = new Set();
let speechRecognition = null;
let speechRecognitionActive = false;
let chatbotImageFile = null;
let speechCommittedText = "";
let doctorConnectUnlocked = false;

function loadSymptoms(){

    if(allSymptoms.length > 0){
        renderSymptoms(allSymptoms);
        return;
    }

    fetch("/predict/symptoms/")
    .then(res=>res.json())
    .then(data=>{
        allSymptoms = data;
        renderSymptoms(allSymptoms);
        attachSearchListener();
    });
}


function renderSymptoms(symptoms){

    const container = document.getElementById("symptomContainer");
    if(!container) return;

    container.innerHTML = "";

    symptoms.forEach(symptom=>{

        const chip = document.createElement("div");
        chip.className = "chip";
        chip.innerText = symptom;

        if(selectedSymptoms.has(symptom))
            chip.classList.add("selected");

        chip.onclick = ()=>{

            if(selectedSymptoms.has(symptom)){
                selectedSymptoms.delete(symptom);
                chip.classList.remove("selected");
            }
            else{
                selectedSymptoms.add(symptom);
                chip.classList.add("selected");
            }

        };

        container.appendChild(chip);
    });

    container.style.maxHeight = "200px";
    container.style.overflowY = "auto";
}


function attachSearchListener(){

    const searchBox = document.getElementById("symptomSearch");
    if(!searchBox) return;

    searchBox.addEventListener("input",function(){

        const value = this.value.toLowerCase();

        if(value === ""){
            renderSymptoms(allSymptoms);
            return;
        }

        const filtered = allSymptoms.filter(symptom =>
            symptom.toLowerCase().includes(value)
        );

        renderSymptoms(filtered);
    });
}


/* ===============================
   RUN ML PREDICTION
================================ */

function runAnalysis(){

    if(selectedSymptoms.size === 0){
        alert("Please select symptoms.");
        return;
    }

    fetch("/predict/predict/",{
        method:"POST",
        headers:{ "Content-Type":"application/json"},
        body: JSON.stringify({
            symptoms:Array.from(selectedSymptoms)
        })
    })
    .then(res=>res.json())
    .then(data=>{
        renderPredictionResult(data);
        showPage("page5");
    })
    .catch(()=>alert("Prediction failed"));
}


function runChatbotPrediction(){

    const chatbotInput = document.getElementById("chatbotInput");
    const message = chatbotInput ? chatbotInput.value.trim() : "";

    if(message === "" && !chatbotImageFile){
        alert("Please write symptoms, use voice typing, or upload a disease image.");
        return;
    }

    const formData = new FormData();
    formData.append("message", message);
    if(chatbotImageFile){
        formData.append("image", chatbotImageFile);
    }

    fetch("/predict/chatbot/",{
        method:"POST",
        body: formData
    })
    .then(async res=>{
        const data = await res.json();

        if(!res.ok){
            throw new Error(data.error || "Chatbot prediction failed");
        }

        return data;
    })
    .then(data=>{
        renderPredictionResult(data);
        showPage("page5");
    })
    .catch(error=>alert(error.message || "Chatbot prediction failed"));
}

function resetAdvisorInputs(){

    stopVoiceTyping();
    chatbotImageFile = null;
    speechCommittedText = "";

    const imageInput = document.getElementById("chatbotImageInput");
    if(imageInput) imageInput.value = "";

    const preview = document.getElementById("chatbotImagePreview");
    if(preview){
        preview.src = "";
        preview.classList.add("hidden");
    }

    updateVoiceStatus("");
    updateImageStatus("");
}

function getSpeechRecognition(){

    if(speechRecognition){
        return speechRecognition;
    }

    const SpeechRecognitionApi = window.SpeechRecognition || window.webkitSpeechRecognition;
    if(!SpeechRecognitionApi){
        return null;
    }

    speechRecognition = new SpeechRecognitionApi();
    speechRecognition.lang = "en-US";
    speechRecognition.interimResults = true;
    speechRecognition.continuous = true;

    speechRecognition.onstart = function(){
        speechRecognitionActive = true;
        const chatbotInput = document.getElementById("chatbotInput");
        speechCommittedText = chatbotInput ? chatbotInput.value.trim() : "";
        syncVoiceButton();
        updateVoiceStatus("Listening... speak your symptoms clearly.");
    };

    speechRecognition.onresult = function(event){
        const chatbotInput = document.getElementById("chatbotInput");
        if(!chatbotInput) return;

        let finalTranscript = "";
        let interimTranscript = "";

        for(let i = event.resultIndex; i < event.results.length; i++){
            const transcript = event.results[i][0].transcript;
            if(event.results[i].isFinal){
                finalTranscript += transcript;
            } else {
                interimTranscript += transcript;
            }
        }

        if(finalTranscript.trim()){
            speechCommittedText = [speechCommittedText, finalTranscript.trim()]
                .filter(Boolean)
                .join(" ")
                .replace(/\s+/g, " ")
                .trim();
        }

        const combinedText = [speechCommittedText, interimTranscript.trim()]
            .filter(Boolean)
            .join(" ")
            .replace(/\s+/g, " ")
            .trim();

        chatbotInput.value = combinedText;
    };

    speechRecognition.onerror = function(event){
        speechRecognitionActive = false;
        syncVoiceButton();

        if(event.error === "not-allowed"){
            updateVoiceStatus("Microphone permission was blocked.");
            return;
        }

        if(event.error === "no-speech"){
            updateVoiceStatus("No speech detected. Try again.");
            return;
        }

        updateVoiceStatus("Voice typing stopped.");
    };

    speechRecognition.onend = function(){
        speechRecognitionActive = false;
        syncVoiceButton();
    };

    return speechRecognition;
}

function toggleVoiceTyping(){

    if(speechRecognitionActive){
        stopVoiceTyping();
        updateVoiceStatus("Voice typing stopped.");
        return;
    }

    const recognition = getSpeechRecognition();
    if(!recognition){
        updateVoiceStatus("Voice typing is not supported in this browser.");
        return;
    }

    const chatbotInput = document.getElementById("chatbotInput");
    speechCommittedText = chatbotInput ? chatbotInput.value.trim() : "";

    recognition.start();
}

function stopVoiceTyping(){

    if(speechRecognition && speechRecognitionActive){
        speechRecognition.stop();
    }
}

function syncVoiceButton(){

    const voiceBtn = document.getElementById("voiceInputBtn");
    if(!voiceBtn) return;

    voiceBtn.innerHTML = speechRecognitionActive
        ? '<i class="fas fa-stop-circle"></i> Stop Voice Typing'
        : '<i class="fas fa-microphone"></i> Start Voice Typing';
}

function updateVoiceStatus(message){

    const voiceStatus = document.getElementById("voiceStatus");
    if(voiceStatus){
        voiceStatus.innerText = message;
    }
}

function updateImageStatus(message){

    const imageStatus = document.getElementById("imageStatus");
    if(imageStatus){
        imageStatus.innerText = message;
    }
}

function handleChatbotImageUpload(event){

    const file = event.target.files && event.target.files[0];
    if(!file){
        chatbotImageFile = null;
        updateImageStatus("");
        return;
    }

    if(!file.type.startsWith("image/")){
        chatbotImageFile = null;
        updateImageStatus("Please upload a valid image file.");
        return;
    }

    if(file.size > 5 * 1024 * 1024){
        chatbotImageFile = null;
        updateImageStatus("Image must be 5 MB or smaller.");
        return;
    }

    const preview = document.getElementById("chatbotImagePreview");
    if(preview){
        preview.src = URL.createObjectURL(file);
        preview.classList.remove("hidden");
    }

    chatbotImageFile = file;
    updateImageStatus("Image added. It will be uploaded for backend analysis when you run the chatbot.");
}


function renderPredictionResult(data){

    document.getElementById("resultDisease").innerText = data.disease || "-";
    document.getElementById("resultSeverity").innerText = data.severity || "-";
    document.getElementById("resultRemedy").innerText = data.remedy || "-";
    document.getElementById("resultAdvice").innerText = data.advice || "-";

    const matchedSymptoms = document.getElementById("resultMatchedSymptoms");
    if(data.matched_symptoms && data.matched_symptoms.length > 0){
        matchedSymptoms.innerText = `Detected symptoms: ${data.matched_symptoms.join(", ")}`;
    } else {
        matchedSymptoms.innerText = "";
    }

    const warning = document.getElementById("resultWarning");
    warning.innerText = data.warning || "";

    const shouldSuggestDoctor = Boolean(data.recommend_doctor_consultation);
    doctorConnectUnlocked = shouldSuggestDoctor;
    closeDoctorConnectModal();

    const doctorSuggestionPanel = document.getElementById("doctorSuggestionPanel");
    const doctorSuggestionText = document.getElementById("doctorSuggestionText");
    if(doctorSuggestionPanel && doctorSuggestionText){
        if(shouldSuggestDoctor){
            doctorSuggestionText.innerText = "This prediction suggests that speaking with a doctor would be a better next step. You can unlock a paid doctor consultation and video call from here.";
            doctorSuggestionPanel.classList.remove("hidden");
        } else {
            doctorSuggestionText.innerText = "";
            doctorSuggestionPanel.classList.add("hidden");
        }
    }
}


/* ===============================
   HISTORY
================================ */

function loadHistory(){

    fetch("/predict/history/")
    .then(res=>res.json())
    .then(data=>{

        const panel = document.getElementById("historyPanel");
        panel.style.display = "block";

        if(data.length === 0){
            panel.innerHTML =
            `<button onclick="closeHistory()" class="btn-back">← Back</button>
             <p>No prediction history yet.</p>`;
            return;
        }

        let html =
        `<button onclick="closeHistory()" class="btn-back">← Back</button>
         <h3>Prediction History</h3>`;

        data.forEach(item=>{
            html += `
                <div style="border:1px solid #444;padding:10px;margin-bottom:10px;">
                    <strong>Disease:</strong> ${item.disease}<br>
                    <strong>Severity:</strong> ${item.severity}<br>
                    <strong>Symptoms:</strong> ${item.symptoms}<br>
                    <small>${item.date}</small>
                </div>`;
        });

        panel.innerHTML = html;
    });
}

function closeHistory(){
    document.getElementById("historyPanel").style.display = "none";
}


function googleLogin(){

    console.log("========== GOOGLE LOGIN FUNCTION CALLED ==========");
    console.log("Current URL:", window.location.href);
    console.log("Current Origin:", window.location.origin);

    if(!auth || !firebaseReady) {
        console.error("Firebase not ready");
        alert("Firebase is still loading. Please wait a moment and try again.");
        return;
    }

    window.loggingIn = true;

    try {
        const provider = new firebase.auth.GoogleAuthProvider();
        provider.addScope('profile');
        provider.addScope('email');
        provider.setCustomParameters({ prompt: 'select_account' });

        console.log("Attempting Google Popup authentication...");

        auth.signInWithPopup(provider)
        .then(result => {
            console.log("Popup login successful");
            handleGoogleLoginSuccess(result.user);
        })
        .catch(error => {
            window.loggingIn = false;
            console.error("Popup auth error", error.code, error.message);

            if(error.code === "auth/unauthorized-domain") {
                alert("This domain is not authorized in Firebase. Add localhost in Firebase Authentication > Settings > Authorized domains.");
                return;
            }

            if(error.code === "auth/popup-blocked") {
                alert("Popup was blocked by browser. Please enable popups for this site.");
                return;
            }

            if(error.code === "auth/cancelled-popup-request") {
                alert("Google sign-in was triggered more than once. Try one click only.");
                return;
            }

            if(error.code === "auth/popup-closed-by-user") {
                alert("Google popup was closed before login finished.");
                return;
            }

            if(error.code === "auth/network-request-failed") {
                alert("Network error. Check your internet connection.");
                return;
            }

            alert("Authentication failed:\n\nCode: " + (error.code || "unknown") + "\nMessage: " + error.message);
        });

    } catch(e) {
        console.error("Google login exception", e.message);
        window.loggingIn = false;
        alert("Error: " + e.message);
    }

}


// Logout function///

function logoutUser(){

    fetch("/accounts/logout/")
    .then(res => res.json())
    .then(data => {

        if(data.success){
            location.reload();
        }

    });

}

// Handle redirect result (Firebase redirect flow)
document.addEventListener("DOMContentLoaded", function() {
    
    console.log("🔧 DOMContentLoaded event fired");
    
    // ========== ATTACH GOOGLE LOGIN BUTTON LISTENER ==========
    attachGoogleButtonListener();
    
});
