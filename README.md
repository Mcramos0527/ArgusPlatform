# ARGUS Web — Wave 3

Sistema web de reconciliación bancaria para Delfabro.

## Stack
- **Backend:** FastAPI (Python) → Koyeb (free, no credit card, always-on)
- **Frontend:** Next.js → Vercel
- **Database:** Supabase (PostgreSQL + Storage)
- **CI/CD:** GitHub Actions + Koyeb auto-deploy

## Setup local

### Backend
```bash
cd backend
pip install -r requirements.txt
cp .env.example .env   # fill in your values
uvicorn app.main:app --reload
```

### Frontend
```bash
cd frontend
npm install
cp .env.example .env.local  # fill in your values
npm run dev
```

## Deploy
- **Backend:** Push to `main` → Koyeb auto-deploys (configured in Koyeb dashboard)
- **Frontend:** Push to `main` → Vercel auto-deploys

## Supabase Setup
Run `supabase/migrations/20260523000000_initial.sql` in Supabase SQL editor.

## Environment Variables

### Backend (Koyeb)
| Var | Description |
|-----|-------------|
| SUPABASE_URL | Your Supabase project URL |
| SUPABASE_SERVICE_KEY | Service role key (secret) |
| SUPABASE_ANON_KEY | Anon public key |
| FRONTEND_URL | Frontend URL for CORS |

### Frontend (Vercel)
| Var | Description |
|-----|-------------|
| NEXT_PUBLIC_BACKEND_URL | Backend API URL |
| NEXT_PUBLIC_SUPABASE_URL | Supabase URL |
| NEXT_PUBLIC_SUPABASE_ANON_KEY | Supabase anon key |
