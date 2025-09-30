```mermaid
erDiagram
    episodes {
        int id PK
        text title
        text audio_url
        int duration
        text status
        timestamp created_at
    }

    transcripts {
        int id PK
        int episode_id FK
        text text
        text segments_json
        timestamp created_at
    }

    summaries {
        int id PK
        int episode_id FK
        text summary_text
        text chapters_json
        text quotes_json
        timestamp created_at
    }

    episodes ||--o{ transcripts : has
    episodes ||--o{ summaries : has

