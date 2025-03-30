# UIL Results Hub

A web-based application for viewing UIL academic competition results, scraping the results from Speechwire. This application allows you to view district and regional results for various UIL academic competitions.

## Features

- View district results for a single region or all regions
- View regional results
- Support for all UIL academic competitions

## Prerequisites

- Python 3.7 or higher
- pip (Python package installer)

## Installation

1. Clone this repository:
```bash
git clone https://github.com/warithr621/uil-hub.git
cd uil-hub
```

2. Create a virtual environment (recommended):
```bash
python -m venv venv
source venv/bin/activate  # On Windows, use: venv\Scripts\activate
```

3. Install the required packages:
```bash
pip install -r requirements.txt
```

## Running the Application

1. Make sure your virtual environment is activated (if you created one)

2. Start the Flask application:
```bash
python app.py
```

3. Open your web browser and navigate to:
```
http://localhost:5000
```
If this doesn't work, check the terminal again, as it may ask you to open it in another location. For example:
```bash
* Running on http://127.0.0.1:5000 # use this website instead of localhost
```

## Usage

1. Select the competition year (2023-2025)
2. Choose the classification (1A-6A)
3. Select the view type:
   - District Results (Single Region)
   - District Results (All Regions)
   - Regional Results (coming soon)
4. Choose the competition
5. If viewing single region results, select the region number
6. Click "Get Results" to view the competition results

## Project Structure

```
uil-hub/
├── app.py              # Main Flask application
├── requirements.txt    # Python dependencies
├── static/
│   └── style.css      # Custom CSS styles
└── templates/
    └── index.html     # Main HTML template
```

## Contributing

Feel free to submit issues and enhancement requests! 