-- Keep the Render backend awake, scheduled from Postgres (2026-07-31).
--
-- ── Why this replaces the GitHub Actions schedule ───────────────────────────
-- `.github/workflows/keepalive.yml` asks for `*/10` — every ten minutes. What
-- it actually got, measured on 2026-07-30:
--
--     16:58Z (51s)   15:20Z (50s)   13:04Z (9s)   11:21Z (42s)   09:11Z (14s)
--
-- Roughly every 90–120 minutes, not every 10. GitHub's scheduled runners are
-- best-effort and drop runs under load. The 42–51 second durations are the
-- tell: each ping was itself paying a cold start, which means the service had
-- already spun down between pings. The workflow was succeeding and doing
-- nothing.
--
-- pg_cron runs inside the database on a real scheduler, so `*/10` means
-- every ten minutes.
--
-- ── Why cold starts are worth this much trouble ─────────────────────────────
-- Measured on the live service, 2026-07-30:
--
--     cold /health                     36.0 s
--     warm /health                      1.2 s
--     first chat query after a restart ~85   s   (Chroma re-ingests lazily on
--                                                 ephemeral disk — KL 28)
--     warm chat query                  29.3 s
--
-- That first-request-after-restart cost is the "dashboard takes a minute"
-- complaint, and it is also what makes the same-origin proxy unsafe: the ~85 s
-- query 502s through Vercel while the 29 s one is comfortable. Removing cold
-- starts fixes the user-visible symptom and unblocks that work at the same time.
--
-- ── Instance hours ─────────────────────────────────────────────────────────
-- Render's free tier allows 750 instance-hours/month. Awake around the clock is
-- ~744 h, which fits with no headroom at all — one busy month or a second
-- service and you are over. This window is 01:00–17:59 UTC (06:30–23:29 IST),
-- about 17 h/day and ~517 h/month, covering the hours the app is used. Outside
-- it, the first request of the day still pays one wake-up.
--
-- To go 24/7, change `1-17` to `*` and watch the Render usage meter.
--
-- ── Run this in the Supabase SQL editor ────────────────────────────────────

create extension if not exists pg_cron;
create extension if not exists pg_net;

-- Idempotent: unschedule first so re-running this file updates the job rather
-- than erroring on a duplicate name.
select cron.unschedule('keepalive-render')
where exists (select 1 from cron.job where jobname = 'keepalive-render');

select cron.schedule(
  'keepalive-render',
  '*/10 1-17 * * *',
  $$
    -- `timeout_milliseconds` is deliberately far above the 1.2 s a warm health
    -- check takes. A cold wake measured 36 s, and pg_net's default 5 s timeout
    -- would abandon the request mid-wake. The wake still happens either way --
    -- Render's router starts the service the moment the request arrives -- but
    -- a timeout is recorded as a failure, which would make the job look broken
    -- exactly when it was doing its job.
    select net.http_get(
      url := 'https://rewardspilotos.onrender.com/api/v1/health',
      timeout_milliseconds := 45000
    );
  $$
);

-- ── Verify ─────────────────────────────────────────────────────────────────
-- The job exists and is active:
--
--     select jobid, jobname, schedule, active from cron.job;
--
-- It is actually firing every ten minutes (this is the thing GitHub failed):
--
--     select start_time, status, return_message
--     from cron.job_run_details
--     where jobname = 'keepalive-render'
--     order by start_time desc
--     limit 12;
--
-- The pings are reaching Render and returning 200. `net._http_response` keeps
-- responses briefly (pg_net prunes them automatically), so check soon after:
--
--     select id, status_code, created
--     from net._http_response
--     order by created desc
--     limit 12;
--
-- The real proof is external: a /health call during the window should return in
-- ~1 s rather than ~36 s.

-- ── To stop it ─────────────────────────────────────────────────────────────
--     select cron.unschedule('keepalive-render');
