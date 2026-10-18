-- Supabase exposes tables in the public schema through its REST API (anon key).
-- Enable Row Level Security with no policies so that API returns nothing.
-- The backend connects as the table owner, which bypasses RLS, so it is unaffected.
ALTER TABLE users ENABLE ROW LEVEL SECURITY;
ALTER TABLE connections ENABLE ROW LEVEL SECURITY;
ALTER TABLE agent_threads ENABLE ROW LEVEL SECURITY;
ALTER TABLE agent_messages ENABLE ROW LEVEL SECURITY;
ALTER TABLE working_memory ENABLE ROW LEVEL SECURITY;
