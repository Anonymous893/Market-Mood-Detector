# Market-Mood-Detector

A dashboard for analysing market sentiment and technical indicators of stocks, featuring real-time composite scoring and historical trend visualisation.

While the python script in the backend allows for all stocks to be analysed, the interactive page only works for Magnificent 7 stocks and locally.


<!-- GETTING STARTED -->
## Getting Started
To get things running locally, follow these steps.

### Prerequisites
Python, NodeJS should already be installed. PostgreSQL should also be installed, if that is the database that is being used. I used SQLite to for local actions.

### Installation

1. Clone the repo
   ```sh
   git clone https://github.com/Anonymous893/Market-Mood-Detector.git
   ```
#### Backend
First, go to the backend directory
    ```sh
    cd backend
    ```
Create and activate virtual environment
    ```sh
   python -m venv venv
   ```
1. Mac/Linux
   ```sh
   source venv/bin/activate
   ```
2. Windows
   ```sh
   venv\Scripts\activate
   ```
Install Python dependencies
    ```sh
    pip install -r requirements.txt
    ```
Set up environment variables in .env file: can get API keys from FRED and World Trading, and database URL

#### Frontend
Go to the frontend directory
    ```sh
    cd frontend
    ```
Install dependencies with
    ```
    npm install
    ```

#### Running
In separate terminals:
1. Terminal 1
    ```
    cd backend
    python app.py
    ```
2. Terminal 2
    ```
    cd frontend
    npm start
    ```

<!-- USAGE EXAMPLES -->
## Screenshots
![Start Page][home-screenshot]
![Analysis Page][analyse-screenshot]
![Specific Stock Page][specific-screenshot]

<!-- MARKDOWN LINKS & IMAGES -->
[home-screenshot]: screenshots/home.png
[analyse-screenshot]: screenshots/analyse.png
[specific-screenshot]: screenshots/specific.png