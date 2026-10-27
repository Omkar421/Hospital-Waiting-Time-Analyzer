# Hospital Waiting Time Analyzer

A student Big Data Analytics project that analyzes hospital waiting times using an interactive Streamlit dashboard. It includes sample data, CSV upload, department/day filters, charts, key findings, and downloadable analysis.

## Features
- Overall patient count, average wait, median wait, and percentage waiting over 30 minutes
- Department-wise average waiting time
- Day-wise waiting trends
- Waiting-time distribution and arrivals by hour
- CSV upload, data validation, filtering, and CSV export
- Separate optional PySpark analysis script

## Run locally
Python 3.10+ recommended.

```bash
python -m venv .venv
# Windows:
.venv\Scripts\activate
# macOS/Linux:
source .venv/bin/activate
pip install -r requirements.txt
streamlit run app.py
```

## Deploy to Streamlit Community Cloud
1. Upload this project to a GitHub repository.
2. Ensure `app.py`, `requirements.txt`, and the `data/` folder are in the repository root.
3. Sign in at https://share.streamlit.io/ (Streamlit Community Cloud).
4. Choose **Create app**, select your repository and branch, and set the main file path to `app.py`.
5. Deploy. Streamlit will install dependencies from `requirements.txt`.

The hosted dashboard runs with pandas for dependable deployment. It does not start a Hadoop cluster or HDFS service.

## Hadoop and Spark component
The optional script `scripts/spark_analysis.py` uses PySpark to calculate the same kinds of summaries in a Spark session. It requires Java and PySpark to be installed in the environment. Example:

```bash
pip install pyspark
spark-submit scripts/spark_analysis.py data/hospital_waiting_data.csv
```

This script is intended for a compatible local or cloud notebook environment. Full Hadoop HDFS requires a separately configured Hadoop environment; Streamlit Community Cloud is not a full Hadoop cluster. For a coursework demonstration, you can show HDFS storage and Spark processing separately, and use Streamlit for the visualization layer.

## Dataset columns
- `Patient_ID`: fictional record ID, not a real patient identity
- `Department`: department name
- `Arrival_Time`: arrival time in 24-hour `HH:MM` format
- `Consultation_Start`: consultation start time in 24-hour `HH:MM` format
- `Day`: weekday

Waiting time is calculated as consultation start minus arrival. A negative difference is treated as an overnight wait. Invalid time records are skipped.

## Privacy and limitations
The bundled dataset is fictional and for educational use. Do not upload real patient-identifying or confidential health data. The sample is small and is not evidence of actual hospital performance. The 30-minute category is an illustrative project threshold, not a clinical standard.

## Project structure
```text
hospital_waiting_time_analyzer/
├── app.py
├── requirements.txt
├── README.md
├── CLAUDE_PROMPT.md
├── data/
│   └── hospital_waiting_data.csv
└── scripts/
    └── spark_analysis.py
```
