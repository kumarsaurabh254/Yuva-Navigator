# SPORTFIT PATHFINDER — GitHub-adapted SIH Prototype

AI-Powered Personalized Sports Discovery and Accessibility Platform

## Important: requirements preserved
- HTML + CSS + vanilla JavaScript
- Python Flask backend
- No React
- No MongoDB
- Dedicated login and account creation pages
- Account must exist before login
- Successful login redirects to `/profile.html`
- No pre-filled questionnaire answers
- Profile data is entered by the user
- Existing prepared ML model integration point: `POST /api/recommend`
- Government facilities and training camps are fictional demo data
- Clear demo-data notices explain that real-life verified data will be available in the product version
- Nutrition guidance section
- Accessibility/inclusive pathways for disabled and third-gender athletes
- Responsive web design
- Restrained, conventional color system
- Server-side password hashing and Flask session authentication for the prototype
- User profile and recommendation are persisted in `backend/users.json` for this prototype

## Run
From the project root:
```bash
cd backend
python -m venv .venv
```
Windows PowerShell:
```powershell
.venv\Scripts\Activate.ps1
```
Then:
```bash
pip install -r requirements.txt
python app.py
```
Open:
`http://127.0.0.1:5000`

## Login flow
Create account -> automatic redirect to My Profile -> complete sports profile -> submit -> recommendation endpoint -> results appear on profile.

Existing account -> Log in -> automatic redirect to My Profile.

If an account does not exist, login returns an error telling the user to create one.

## ML
Open `backend/app.py` and replace the clearly marked demo section inside `/api/recommend` with your already-prepared Python model. The UI and profile flow do not need React or a database to integrate with the model.

## Production security
The prototype uses Flask sessions and hashed passwords, but before real deployment you should set a strong `SPORTFIT_SECRET_KEY`, use HTTPS, move user storage to a real database, add CSRF protection/rate limiting/email verification and keep secrets outside source control.

## GitHub adaptation
See `GITHUB_SOURCE_NOTES.md` for the exact repository used as the structural starting point and the adaptation boundaries.
