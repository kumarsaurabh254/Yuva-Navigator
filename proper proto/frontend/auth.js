async function postJSON(url,data){
  const res=await fetch(url,{
    method:"POST",
    headers:{"Content-Type":"application/json"},
    credentials:"same-origin",
    body:JSON.stringify(data)
  });
  const body=await res.json().catch(()=>({error:"Unexpected server response"}));
  if(!res.ok) throw new Error(body.error||"Request failed");
  return body;
}

function showError(message){
  const e=document.getElementById("error");
  e.textContent=message;
  e.classList.add("show");
}

function clearError(){
  const e=document.getElementById("error");
  e.textContent="";
  e.classList.remove("show");
}

const loginForm=document.getElementById("loginForm");
if(loginForm){
  loginForm.addEventListener("submit",async e=>{
    e.preventDefault();
    clearError();
    try{
      await postJSON("/api/login",{
        email:document.getElementById("email").value.trim(),
        password:document.getElementById("password").value
      });
      window.location.href="/profile.html";
    }catch(err){showError(err.message)}
  });
}

const signupForm=document.getElementById("signupForm");
if(signupForm){
  const password=document.getElementById("password");
  const confirm=document.getElementById("confirm");
  const status=document.getElementById("passwordStatus");
  const show=document.getElementById("showPasswords");

  function validatePasswords(){
    const p=password.value;
    const c=confirm.value;
    if(!c){
      status.textContent="";
      status.className="field-hint";
      confirm.setCustomValidity("");
      return false;
    }
    if(p!==c){
      status.textContent="Passwords do not match.";
      status.className="field-hint invalid";
      confirm.setCustomValidity("Passwords do not match.");
      return false;
    }
    if(p.length<6){
      status.textContent="Use at least 6 characters.";
      status.className="field-hint invalid";
      confirm.setCustomValidity("Password must be at least 6 characters.");
      return false;
    }
    status.textContent="Passwords match ✓";
    status.className="field-hint valid";
    confirm.setCustomValidity("");
    return true;
  }

  password.addEventListener("input",()=>{clearError();validatePasswords()});
  confirm.addEventListener("input",()=>{clearError();validatePasswords()});

  show.addEventListener("change",()=>{
    const type=show.checked?"text":"password";
    password.type=type;
    confirm.type=type;
  });

  signupForm.addEventListener("submit",async e=>{
    e.preventDefault();
    clearError();

    const name=document.getElementById("name").value.trim();
    const email=document.getElementById("email").value.trim();
    const p=password.value;
    const c=confirm.value;

    if(!name){showError("Please enter your full name.");return}
    if(!email){showError("Please enter your email address.");return}
    if(p.length<6){showError("Password must be at least 6 characters.");password.focus();return}
    if(p!==c){showError("Passwords do not match. Please enter the same password in both fields.");confirm.focus();return}

    try{
      await postJSON("/api/register",{name,email,password:p});
      window.location.href="/profile.html";
    }catch(err){showError(err.message)}
  });
}
