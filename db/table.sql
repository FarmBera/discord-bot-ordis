-- party table
CREATE TABLE IF NOT EXISTS party
(
    id            BIGINT UNSIGNED AUTO_INCREMENT,
    thread_id     BIGINT UNSIGNED UNIQUE,
    message_id    BIGINT UNSIGNED UNIQUE,
    host_id       BIGINT UNSIGNED,
    title         TEXT,
    game_name     TEXT,
    departure     DATETIME          DEFAULT CURRENT_TIMESTAMP,
    max_users     INTEGER,
    `description` TEXT,
    `status`      VARCHAR(20)       DEFAULT '모집 중',
    created_at    DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at    DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    PRIMARY KEY (id)
) DEFAULT CHARSET = 'utf8mb4'
;

CREATE TABLE IF NOT EXISTS participants
(
    party_id     BIGINT UNSIGNED,
    user_id      BIGINT UNSIGNED,
    user_mention TEXT,
    display_name TEXT,
    created_at   DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at   DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    PRIMARY KEY (party_id, user_id),
    FOREIGN KEY (party_id) REFERENCES party (id) ON DELETE CASCADE
) DEFAULT CHARSET = 'utf8mb4'
;

-- trade table
CREATE TABLE IF NOT EXISTS trade
(
    id            BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
    host_id       BIGINT UNSIGNED NOT NULL,
    game_nickname TEXT            NOT NULL,
    trade_type    VARCHAR(10)     NOT NULL,                -- sell, buy
    item_name     TEXT            NOT NULL,
    item_rank     INTEGER         NOT NULL DEFAULT 0,
    quantity      INTEGER         NOT NULL,
    price         INTEGER         NOT NULL,
    thread_id     BIGINT UNSIGNED UNIQUE,
    message_id    BIGINT UNSIGNED UNIQUE,
    `status`      VARCHAR(20)              DEFAULT 'open', -- open, close
    created_at    DATETIME        NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at    DATETIME        NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    PRIMARY KEY (id)
) DEFAULT CHARSET = 'utf8mb4'
;

-- user warnings
/*
경고 이력 테이블
- 언제, 무슨 이유(note)로 경고를 받았는지 기록
- 경고 횟수: COUNT(user_id)
 */
CREATE TABLE IF NOT EXISTS warnings
(
    id            BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
    user_id       BIGINT UNSIGNED NOT NULL,
    display_name  VARCHAR(100)    NOT NULL,           -- 경고 당시 닉네임 기록 (스냅샷용)
    game_nickname VARCHAR(150)    NOT NULL,
    category      VARCHAR(20)     NOT NULL,           -- 신고 사유 (예: '욕설', '도배' 등)
    note          VARCHAR(500),                       -- 사유 상세
    given_name    VARCHAR(300)    NOT NULL,           -- 경고 부여자
    critical      BOOLEAN         NOT NULL DEFAULT 0, -- 강력 경고 (임시 벤)
    banned        BOOLEAN         NOT NULL DEFAULT 0, -- 이 경고로 인해 밴 처리가 되었는지 여부
    created_at    DATETIME        NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at    DATETIME        NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    PRIMARY KEY (id)
) DEFAULT CHARSET = 'utf8mb4'
;

-- store admin user
CREATE TABLE admins
(
    user_id      BIGINT UNSIGNED,
    `key`        VARCHAR(50) UNIQUE, -- for fast query
    note         VARCHAR(150),
    super_user   BOOLEAN  NOT NULL DEFAULT FALSE,
    is_dm_target BOOLEAN  NOT NULL DEFAULT FALSE,
    created_at   DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at   DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    PRIMARY KEY (user_id)
) DEFAULT CHARSET = 'utf8mb4'
;

-- other variables
CREATE TABLE IF NOT EXISTS vari
(
    name       VARCHAR(100) NOT NULL,
    `value`    VARCHAR(300) NOT NULL,
    note       VARCHAR(255),
    created_at DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    PRIMARY KEY (name)
) DEFAULT CHARSET = 'utf8mb4'
;

-- notification webhooks
CREATE TABLE IF NOT EXISTS webhooks
(
    channel_id      BIGINT UNSIGNED NOT NULL,
    guild_id        BIGINT UNSIGNED NOT NULL,
    webhook_url     TEXT            NOT NULL,
    note            VARCHAR(300),
    created_at      DATETIME        NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at      DATETIME        NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    -- notification flags (1: ON, 0: OFF)
    sub_alerts      BOOLEAN         NOT NULL DEFAULT 0, -- alert mission
    sub_news        BOOLEAN         NOT NULL DEFAULT 0, -- warfrane mews
    sub_sortie      BOOLEAN         NOT NULL DEFAULT 0, -- sortie
    sub_archonhunt  BOOLEAN         NOT NULL DEFAULT 0, -- archon hunt
    sub_voidtraders BOOLEAN         NOT NULL DEFAULT 0, -- baro ki teer
    sub_steelpath   BOOLEAN         NOT NULL DEFAULT 0, -- steel essense (teshin)
    sub_darchimedea BOOLEAN         NOT NULL DEFAULT 0, -- deep archimedea
    sub_tarchimedea BOOLEAN         NOT NULL DEFAULT 0, -- temporal archimedea
    sub_calendar    BOOLEAN         NOT NULL DEFAULT 0, -- 1999 calendar
    sub_dailydeals  BOOLEAN         NOT NULL DEFAULT 0, -- daily deals
    sub_invasions   BOOLEAN         NOT NULL DEFAULT 0, -- invasions
    sub_duviri_wf   BOOLEAN         NOT NULL DEFAULT 0, -- circuit warframe
    sub_duviri_inc  BOOLEAN         NOT NULL DEFAULT 0, -- circuit incarnon
    sub_events      BOOLEAN         NOT NULL DEFAULT 0, -- periodic events
    sub_cetus       BOOLEAN         NOT NULL DEFAULT 0, -- cetus worldstate
    sub_duviri      BOOLEAN         NOT NULL DEFAULT 0, -- duviri worldstate
    sub_cambion     BOOLEAN         NOT NULL DEFAULT 0, -- cambion worldstate
    sub_vallis      BOOLEAN         NOT NULL DEFAULT 0, -- vallis worldstate
    PRIMARY KEY (channel_id)
) DEFAULT CHARSET = 'utf8mb4'
;

-- improved log table
CREATE TABLE IF NOT EXISTS `logs`
(
    id           BIGINT UNSIGNED AUTO_INCREMENT,
    `type`       VARCHAR(15)  NOT NULL,
    -- user info
    display_name VARCHAR(200),
    global_name  VARCHAR(200),
    user_name    VARCHAR(200),
    user_id      BIGINT UNSIGNED,
    -- guild info
    guild_name   VARCHAR(200),
    guild_id     BIGINT UNSIGNED,
    -- channel info
    channel_name VARCHAR(200),
    channel_id   BIGINT UNSIGNED,
    -- content
    created_at   DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP,
    cmd          VARCHAR(200),
    msg          VARCHAR(500) NOT NULL,
    PRIMARY KEY (id)
) DEFAULT CHARSET = 'utf8mb4'
;

-- detailed log content
CREATE TABLE IF NOT EXISTS log_detail
(
    log_id  BIGINT UNSIGNED,
    content MEDIUMTEXT,
    PRIMARY KEY (log_id),
    FOREIGN KEY (log_id) REFERENCES `logs` (id) ON DELETE CASCADE
) DEFAULT CHARSET = 'utf8mb4'
;

-- approved guild & save channels
CREATE TABLE IF NOT EXISTS channels
(
    guild_id    BIGINT UNSIGNED,
    party_ch    BIGINT UNSIGNED,
    trade_ch    BIGINT UNSIGNED,
    complain_ch BIGINT UNSIGNED,
    warn_log_ch BIGINT UNSIGNED,
    is_allowed  BOOLEAN  NOT NULL DEFAULT FALSE,
    note        VARCHAR(300),
    created_at  DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at  DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    PRIMARY KEY (guild_id)
) DEFAULT CHARSET = 'utf8mb4'
;


-- voice logging table
CREATE TABLE voice
(
    id           BIGINT       NOT NULL AUTO_INCREMENT PRIMARY KEY,
    user_id      BIGINT       NOT NULL,
    user_name    VARCHAR(100) NOT NULL,
    display_name VARCHAR(100) NOT NULL,
    channel      VARCHAR(200) NOT NULL,
    joined_at    TIMESTAMP    NOT NULL DEFAULT CURRENT_TIMESTAMP,
    left_at      TIMESTAMP    NULL     DEFAULT NULL,
    duration_sec INT          NULL     DEFAULT NULL,
    INDEX idx_open_session (user_id, left_at)
) ENGINE = InnoDB
  DEFAULT CHARSET = utf8mb4;