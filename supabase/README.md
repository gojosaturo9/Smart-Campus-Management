# Supabase Migrations

Run these files from the Supabase SQL Editor in this order:

1. `schema.sql`
2. `shared_attendance_source.sql`

The platform reads Supabase connection values from environment variables first:

- `SUPABASE_URL`
- `SUPABASE_ANON_KEY`
- `SUPABASE_SERVICE_ROLE_KEY`

`secrets.toml` is still supported for local legacy setups, but `.env` or deployment environment variables are the production path.
