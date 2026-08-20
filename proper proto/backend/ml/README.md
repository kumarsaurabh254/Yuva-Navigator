# SportFit Pathfinder ML integration

Your prepared model is not recreated here.

The integration point is:
`POST /api/recommend`

The profile payload is:
```json
{
  "age": 18,
  "location": "Example District",
  "goal": "Fitness",
  "activity": "Moderate",
  "accessibility": "None",
  "budget": "Under ₹500"
}
```

Replace the clearly marked demo block in `backend/app.py` with your model loading, preprocessing and inference.

Keep the response shape:
```json
{
  "demo": false,
  "sports": [
    {"sport": "Badminton", "score": 0.92}
  ]
}
```
