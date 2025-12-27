-- Chatbot feature table for company-specific AI conversations
-- Run this migration after schema.sql to add chatbot functionality

CREATE TABLE IF NOT EXISTS chat_message (
    chat_message_id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT NOT NULL,
    company_id INT NOT NULL,
    conversation_session_id VARCHAR(36) NOT NULL,
    message_text TEXT NOT NULL,
    is_user_message BOOLEAN NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    FOREIGN KEY (user_id) REFERENCES USER(user_id) ON DELETE CASCADE,
    FOREIGN KEY (company_id) REFERENCES COMPANY(company_id) ON DELETE CASCADE,

    INDEX idx_user_company (user_id, company_id),
    INDEX idx_session (conversation_session_id),
    INDEX idx_created_at (created_at)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;