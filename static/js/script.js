function getCSRFToken() {
    return document.getElementById("csrfToken").value;
}


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

        renderSymptoms(allSymptoms);
    }
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

    })
    .catch(()=>{
        document.getElementById("displayName").innerText = "User";
    });
}


/* ===============================
   SIGN IN (SEND OTP)
================================ */

function handleSignIn(e){

    e.preventDefault();

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
    })
    .then(res=>res.json())
    .then(data=>{

        if(data.success){
            showOTPModal();
        }
        else{
            alert(data.message || "Unable to send OTP");
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


/* OTP Auto Focus */

document.addEventListener("DOMContentLoaded", ()=>{

    document.querySelectorAll(".otp-digit")
    .forEach((input,index,arr)=>{

        input.addEventListener("input",()=>{
            if(input.value && arr[index+1]){
                arr[index+1].focus();
            }
        });

        input.addEventListener("keydown",(e)=>{
            if(e.key==="Backspace" && !input.value && arr[index-1]){
                arr[index-1].focus();
            }
        });

    });

});


/* ===============================
   SYMPTOMS
================================ */

let allSymptoms = [];
let selectedSymptoms = new Set();

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

        document.getElementById("resultDisease").innerText = data.disease;
        document.getElementById("resultSeverity").innerText = data.severity;
        document.getElementById("resultRemedy").innerText = data.remedy;
        document.getElementById("resultAdvice").innerText = data.advice;

        showPage("page5");

    })
    .catch(()=>alert("Prediction failed"));
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
