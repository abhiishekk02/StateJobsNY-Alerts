CREATE TABLE IF NOT EXISTS subscribers (
  id TEXT PRIMARY KEY,
  email TEXT NOT NULL UNIQUE COLLATE NOCASE,
  name TEXT NOT NULL,
  graduation_year INTEGER NOT NULL,
  roles TEXT NOT NULL,
  locations TEXT NOT NULL,
  status TEXT NOT NULL DEFAULT 'pending' CHECK(status IN ('pending','active','unsubscribed')),
  verification_hash TEXT NOT NULL,
  unsubscribe_hash TEXT NOT NULL,
  consented_at TEXT NOT NULL,
  verified_at TEXT,
  unsubscribed_at TEXT,
  created_at TEXT NOT NULL,
  updated_at TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_subscribers_status ON subscribers(status);
CREATE UNIQUE INDEX IF NOT EXISTS idx_subscribers_verify ON subscribers(verification_hash);
CREATE UNIQUE INDEX IF NOT EXISTS idx_subscribers_unsubscribe ON subscribers(unsubscribe_hash);
CREATE TABLE IF NOT EXISTS deliveries (
  subscriber_id TEXT NOT NULL,
  job_id TEXT NOT NULL,
  delivered_at TEXT NOT NULL,
  PRIMARY KEY (subscriber_id, job_id),
  FOREIGN KEY (subscriber_id) REFERENCES subscribers(id) ON DELETE CASCADE
);
