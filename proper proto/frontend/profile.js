// ==========================================
// SportFit Pathfinder - Profile Integration
// ==========================================

const profileForm = document.getElementById("profileForm");

const recommendationTitle =
  document.getElementById("recommendationTitle");

const recommendationText =
  document.getElementById("recommendationText");

const results =
  document.getElementById("results");


// ------------------------------------------
// Load saved user information
// ------------------------------------------

function loadUserInfo() {

    const user =
        JSON.parse(localStorage.getItem("user") || "{}");

    const name =
        user.name || user.username || "Athlete";

    const email =
        user.email || "";

    const welcome =
        document.getElementById("welcome");

    const sideName =
        document.getElementById("sideName");

    const sideEmail =
        document.getElementById("sideEmail");

    const avatar =
        document.getElementById("avatar");


    if (welcome) {
        welcome.textContent =
            `Welcome, ${name}`;
    }

    if (sideName) {
        sideName.textContent = name;
    }

    if (sideEmail) {
        sideEmail.textContent = email;
    }

    if (avatar) {
        avatar.textContent =
            name.substring(0, 2).toUpperCase();
    }
}


// ------------------------------------------
// Submit profile
// ------------------------------------------

profileForm.addEventListener("submit", async function(event) {

    event.preventDefault();


    // --------------------------------------
    // Read values from the form
    // --------------------------------------

    const age =
        Number(document.getElementById("age").value);

    const height_cm =
        Number(document.getElementById("height_cm").value);

    const weight_kg =
        Number(document.getElementById("weight_kg").value);

    const gender =
        document.getElementById("gender").value;

    const para_athlete =
        document.getElementById("para_athlete").value === "true";

    const location =
        document.getElementById("location").value;

    const goal =
        document.getElementById("goal").value;

    const activity =
        document.getElementById("activity").value;

    const accessibility =
        document.getElementById("accessibility").value;

    const budget =
        document.getElementById("budget").value;


    // --------------------------------------
    // Basic validation
    // --------------------------------------

    if (!age || !height_cm || !weight_kg) {

        alert(
            "Please enter your age, height and weight."
        );

        return;
    }


    if (!gender) {

        alert(
            "Please select your gender."
        );

        return;
    }


    // --------------------------------------
    // Show loading state
    // --------------------------------------

    recommendationTitle.textContent =
        "Generating your recommendation...";

    recommendationText.textContent =
        "Please wait while our sports guidance system analyzes your profile.";

    results.innerHTML = "";


    const submitButton =
        profileForm.querySelector("button[type='submit']");

    submitButton.disabled = true;

    submitButton.textContent =
        "Generating...";


    // --------------------------------------
    // Data sent to Flask
    // --------------------------------------

    const profileData = {

        age: age,

        height_cm: height_cm,

        weight_kg: weight_kg,

        gender: gender,

        para_athlete: para_athlete,

        location: location,

        goal: goal,

        activity: activity,

        accessibility: accessibility,

        budget: budget
    };


    console.log(
        "Sending profile to backend:",
        profileData
    );


    try {

        // ----------------------------------
        // Call Flask backend
        // ----------------------------------

        const response =
            await fetch("/api/recommend", {

                method: "POST",

                headers: {
                    "Content-Type": "application/json"
                },

                body: JSON.stringify(profileData)
            });


        // ----------------------------------
        // Check server response
        // ----------------------------------

        if (!response.ok) {

            throw new Error(
                `Server returned ${response.status}`
            );
        }


        const data =
            await response.json();


        console.log(
            "Backend response:",
            data
        );


        // ----------------------------------
        // Display recommendation
        // ----------------------------------

        if (data.success === false) {

            throw new Error(
                data.error ||
                "Unable to generate recommendation."
            );
        }


        const sport =
            data.recommended_sport ||
            data.sport ||
            data.recommendation ||
            "No recommendation";


        recommendationTitle.textContent =
            sport;


        recommendationText.textContent =
            data.message ||
            "Based on your profile, this sport is recommended for you.";


        // ----------------------------------
        // Additional information
        // ----------------------------------

        let extraInformation = "";


        if (data.para_recommendation) {

            extraInformation += `
                <p>
                    <strong>Para-sport guidance:</strong>
                    ${data.para_recommendation}
                </p>
            `;
        }


        if (data.gender_note) {

            extraInformation += `
                <p>
                    <strong>Profile guidance:</strong>
                    ${data.gender_note}
                </p>
            `;
        }


        if (data.confidence !== undefined) {

            extraInformation += `
                <p>
                    <strong>Model confidence:</strong>
                    ${data.confidence}%
                </p>
            `;
        }


        results.innerHTML = `

            <div class="recommendation-card">

                <h3>
                    Recommended Sport
                </h3>

                <div class="recommended-sport">
                    ${sport}
                </div>

                ${extraInformation}

            </div>

        `;


    } catch (error) {

        console.error(
            "Recommendation error:",
            error
        );


        recommendationTitle.textContent =
            "Unable to generate recommendation";


        recommendationText.textContent =
            "The website could not connect to the sports guidance backend.";


        results.innerHTML = `

            <div class="recommendation-card">

                <p>
                    Please make sure the backend server is running
                    and try again.
                </p>

                <p>
                    <strong>Error:</strong>
                    ${error.message}
                </p>

            </div>

        `;

    } finally {

        // ----------------------------------
        // Restore button
        // ----------------------------------

        submitButton.disabled = false;

        submitButton.textContent =
            "Generate personalized recommendations";
    }

});


// ------------------------------------------
// Logout
// ------------------------------------------

const logoutButton =
    document.getElementById("logout");

if (logoutButton) {

    logoutButton.addEventListener(
        "click",
        function() {

            localStorage.removeItem("user");

            window.location.href =
                "index.html";
        }
    );
}


// ------------------------------------------
// Initialize page
// ------------------------------------------

loadUserInfo();