# PartnerAI

PartnerAI is an intelligent, personalized AI mentor designed to help you organize your life, stay productive, and grow. It combines a **Telegram Bot** and a **Web Dashboard** to provide a seamless experience.

## ✨ Features

*   **Personalized AI Mentor**: Uses the **NVIDIA API** to chat with you, respecting your goals and personality.
*   **Web Dashboard**: A beautiful interface to view your stats, join communities, and manage tasks.
*   **Productivity Tools**:
    *   **Daily Tasks**: AI-generated tasks to help you reach your goals.
    *   **Focus Mode**: A distraction-free mode with music and wallpapers.
    *   **Reminders**: Smart NLP reminders (e.g., "remind me to gym in 10 mins").
*   **Community Features**: Join groups, chat with others, and work on shared goals.
*   **Gamification**: Earn rewards (flowers, badges) for completing tasks and staying consistent.

## 🛠️ Tech Stack

*   **Backend**: Python (Flask)
*   **AI Inference**: NVIDIA API
*   **Database**: SQLite
*   **Frontend**: HTML, CSS, JavaScript (Vanilla)
*   **Messaging**: Python-Telegram-Bot

## 🚀 Getting Started

### Prerequisites

1.  **Python 3.9+** installed.
2.  Set your **NVIDIA API key** in the environment as `NVIDIA_API_KEY` or `NVAPI_API_KEY`.

### Deploying on Vercel

Set these environment variables in Vercel:

* `NVIDIA_API_KEY`
* `NVIDIA_MODEL` (optional)
* `BOT_TOKEN` (if you use the Telegram bot)
* `PARTNERAI_DB_PATH` (optional; defaults to `/tmp/partnerai.db` on Vercel)

### Installation

1.  Clone the repository:
    ```bash
    git clone https://github.com/your-username/PartnerAI.git
    cd PartnerAI
    ```

2.  Install dependencies:
    ```bash
    pip install -r requirements.txt
    ```

3.  Configure the environment:
    *   Rename `config.example.py` to `config.py`.
    *   Add your **Telegram Bot Token** in `config.py`.
    *   Add your **NVIDIA API key** in your deployment environment.

### Running the App

1.  **Start the Web Interface**:
    ```bash
    python web/app.py
    ```
    Access it at `http://localhost:5000`.

2.  **Start the Telegram Bot** (Optional):
    ```bash
    python partnerai.py
    ```

## 🤝 Contributing

Feel free to fork this repository and submit pull requests. Suggestions are welcome!

## 📜 License

This project is open-source.
