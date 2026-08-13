-- CRM Database Schema
-- Banco de dados para gerenciar leads, interações e conversões

CREATE TABLE IF NOT EXISTS crm_leads (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  name TEXT NOT NULL,
  email TEXT UNIQUE NOT NULL,
  phone TEXT,
  interest VARCHAR(50) NOT NULL, -- construction, investment, partnership, financing, consulting
  source VARCHAR(50) NOT NULL DEFAULT 'website', -- website, whatsapp, crm_direct, referral
  initial_score INT CHECK (initial_score >= 0 AND initial_score <= 100),
  final_score INT CHECK (final_score >= 0 AND final_score <= 100),
  status VARCHAR(50) DEFAULT 'new', -- new, contacted, qualified, rejected, converted
  assigned_module VARCHAR(50), -- OPERA, CEA, P&D, STRATEGY, SALES
  estimated_value TEXT,
  created_by VARCHAR(100) DEFAULT 'john_crm',
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  qualified_at TIMESTAMP,
  converted_at TIMESTAMP,
  project_id UUID,
  deal_id UUID,
  UNIQUE(email)
);

CREATE INDEX idx_crm_leads_status ON crm_leads(status);
CREATE INDEX idx_crm_leads_score ON crm_leads(final_score DESC);
CREATE INDEX idx_crm_leads_module ON crm_leads(assigned_module);
CREATE INDEX idx_crm_leads_created ON crm_leads(created_at DESC);

-- Interacoes (mensagens, chamadas, emails)
CREATE TABLE IF NOT EXISTS crm_interactions (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  lead_id UUID NOT NULL REFERENCES crm_leads(id) ON DELETE CASCADE,
  type VARCHAR(50) NOT NULL, -- message, call, email, suggestion, video
  content TEXT NOT NULL,
  john_response TEXT,
  sentiment VARCHAR(20) DEFAULT 'neutral', -- positive, neutral, negative
  interaction_timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  duration_seconds INT
);

CREATE INDEX idx_crm_interactions_lead ON crm_interactions(lead_id);
CREATE INDEX idx_crm_interactions_sentiment ON crm_interactions(sentiment);

-- Conversoes e projetos gerados
CREATE TABLE IF NOT EXISTS crm_conversions (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  lead_id UUID NOT NULL REFERENCES crm_leads(id),
  project_id UUID NOT NULL,
  deal_id UUID NOT NULL,
  deal_type VARCHAR(50) NOT NULL, -- construction, investment, service
  deal_value DECIMAL(15, 2),
  conversion_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_crm_conversions_lead ON crm_conversions(lead_id);
CREATE INDEX idx_crm_conversions_project ON crm_conversions(project_id);

-- Auditoria: quem fez o quê quando
CREATE TABLE IF NOT EXISTS crm_audit_log (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  lead_id UUID NOT NULL,
  action VARCHAR(100) NOT NULL,
  actor VARCHAR(100) NOT NULL DEFAULT 'john_crm',
  details JSONB,
  timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_crm_audit_lead ON crm_audit_log(lead_id);
CREATE INDEX idx_crm_audit_actor ON crm_audit_log(actor);
