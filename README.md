# 📊 WhatsApp Chat Analyzer & User Activity Classifier

A powerful Streamlit web application that analyzes WhatsApp group chat data to generate insightful visualizations, statistics, and **predicts whether a user is highly active (1) or not (0)** using machine learning models.

---
[ Please copy this url and paste it into a new tab ]
You can visit the site at :
https://chat-analyze.streamlit.app/

## 🚀 Features

- 📈 Monthly & Daily timelines of chat activity  
- 🗓️ Weekly activity heatmaps  
- 🧍 Most active users, message counts, media & link shares  
- ☁️ WordCloud of most used words  
- 🔡 Emoji and text statistics  
- 🤖 ML-based classification of users into active/inactive  
- 📊 Evaluation of Logistic Regression, KNN, Decision Tree (Tuned & Untuned)

---

## 🧠 ML Classification Models

The project uses three models to classify users:
- **Logistic Regression**
- **K-Nearest Neighbors (KNN)**
- **Decision Tree**

Each model is evaluated using:
- Confusion Matrix  
- Accuracy, Precision, Recall, F1 Score  
- Classification Reports (Train & Test)  
- Comparison of model performance (Tuned vs Non-Tuned)

---

## 📁 Dataset Description

- **Source**: Exported `.txt` file from WhatsApp  
- **Parsed using regex** to extract:
  - Date & Time
  - Sender Name
  - Message content
  - Emoji usage
  - Media/Link sharing
  - Hour, Day, Month, etc.

---

## 📊 Extracted Features for ML

| Feature Name      | Description                                  |
|-------------------|----------------------------------------------|
| Message_Length    | Length of each message (in characters)       |
| Emoji_Count       | Number of emojis in a message                |
| Link_Count        | Number of links in a message                 |
| Media_Count       | Binary indicator for media sharing          |
| Hour              | Hour of message sent (0–23)                  |
| DayName           | Day of the week (Monday–Sunday)             |
| is_active         | Target class (1 if user is highly active)    |

---

## 🔧 Tech Stack

| Tool/Library      | Purpose                                      |
|-------------------|----------------------------------------------|
| `Python 3.x`      | Core programming language                    |
| `Streamlit`       | Web application frontend                     |
| `Pandas`          | Data handling and preprocessing              |
| `Matplotlib` & `Seaborn` | Data visualization                  |
| `WordCloud`       | Generating wordclouds from messages          |
| `Emoji`           | Extracting emojis from messages              |
| `Sklearn`         | ML models, metrics, preprocessing            |
| `Regex`           | Parsing raw WhatsApp text format             |

---

## 🧪 Evaluation Metrics

Models were tested using:

- Train-Test Accuracy
- Precision, Recall, F1 Score
- Confusion Matrices
- Comparative Chart (Tuned vs Non-Tuned)

---
## 📁 Folder Structure
│
├── app.py # Main Streamlit app
├── helper.py # Functions for visualization & stats
├── preprocessor.py # WhatsApp text parsing logic
├── ml_models.py # ML model training, tuning, evaluation
├── requirements.txt # Python dependencies
└── README.md # Project documentation
