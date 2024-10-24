import streamlit as st
from pymongo import MongoClient
from datetime import datetime
import requests
import plotly.graph_objects as go
# MongoDB connection setup
client = MongoClient("mongodb+srv://deepakqurinom:storeflaunt@cluster0.khjjbpl.mongodb.net/")  # MongoDB connection string
db = client["storeflaunt"]  # Database name
collection = db["classified_reviews"]  # Collection name

# Hugging Face API setup
API_URL = "https://api-inference.huggingface.co/models/lxyuan/distilbert-base-multilingual-cased-sentiments-student"
headers = {"Authorization": "Bearer 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"}

# Function to query Hugging Face API for sentiment analysis
def query_review_sentiment(review_text):
    response = requests.post(API_URL, headers=headers, json={"inputs": review_text})
    result = response.json()
    if response.status_code == 200:
        # Get the label with the highest score
        label = max(result[0], key=lambda x: x['score'])['label']
        return label
    else:
        st.error("Error in sentiment classification API call.")
        return "unknown"

# Sidebar navigation for the two pages
st.sidebar.title("Navigation")
page = st.sidebar.radio("Go to", ["Submit a Review", "Search Reviews"])

# Page 1: Review Submission
if page == "Submit a Review":
    st.title("Submit a Review")

    # Input fields for name and review
    name = st.text_input("Enter your name")
    review = st.text_area("Enter your review")

    # Submit button
    if st.button("Submit"):
        if name and review:
            # Get sentiment label using Hugging Face API
            sentiment_label = query_review_sentiment(review)

            # Create a document to insert
            review_data = {
                "Reviewer_Name": name,
                "Review_Text": review,
                "Date_and_Time": datetime.now(),  # Store current date/time for the review
                "Sentiment_Label": sentiment_label  # Store sentiment label
            }
            # Insert the document into MongoDB
            collection.insert_one(review_data)
            st.success(f"Review submitted successfully! Sentiment: {sentiment_label}")
        else:
            st.error("Please fill in both name and review.")

# Page 2: Search Reviews by Date Range
elif page == "Search Reviews":
    st.title("Search Reviews by Date Range")

    # Create date input widgets for "From" and "To" date selection
    from_date = st.date_input("From Date", value=datetime(2024, 1, 1))
    to_date = st.date_input("To Date", value=datetime(2024, 12, 31))

    # Convert Streamlit date input to datetime for MongoDB query
    from_datetime = datetime.combine(from_date, datetime.min.time())
    to_datetime = datetime.combine(to_date, datetime.max.time())

    # Search button
    if st.button("Search Reviews"):
        # Query to filter reviews within the date range
        query = {
            "Date_and_Time": {
                "$gte": from_datetime,
                "$lte": to_datetime
            }
        }

        # Execute the query and sort by date in descending order
        reviews = collection.find(query).sort("Date_and_Time", -1)
        review_list = list(reviews)

        # Initialize lists to classify reviews by sentiment
        positive_reviews = []
        neutral_reviews = []
        negative_reviews = []

        # Classify reviews by sentiment
        for review in review_list:
            if review['Sentiment_Label'] == 'positive':
                positive_reviews.append(review)
            elif review['Sentiment_Label'] == 'neutral':
                neutral_reviews.append(review)
            elif review['Sentiment_Label'] == 'negative':
                negative_reviews.append(review)

        # Plot the donut chart
        labels = ['Positive', 'Neutral', 'Negative']
        values = [len(positive_reviews), len(neutral_reviews), len(negative_reviews)]

        # Total number of reviews
        total_reviews = len(positive_reviews) + len(neutral_reviews) + len(negative_reviews)

        # Create the donut chart with total reviews in the center
        fig = go.Figure(data=[go.Pie(labels=labels, values=values, hole=.5)])
        fig.update_traces(textinfo='percent+label')
        
        # Add total reviews annotation in the center
        fig.update_layout(
            title_text='Sentiment Distribution of Reviews',
            annotations=[dict(text=f"Total: {total_reviews}", x=0.5, y=0.5, font_size=20, showarrow=False)]
        )

        st.plotly_chart(fig)

        # Display classified reviews by sentiment in tabs
        st.subheader("Reviews by Sentiment")
        tabs = st.tabs(["Positive", "Neutral", "Negative"])

        # Positive Reviews Tab
        with tabs[0]:
            st.write(f"Positive Reviews ({len(positive_reviews)})")
            for review in positive_reviews:
                st.write(f"Reviewer: {review['Reviewer_Name']}")
                st.write(f"Review: {review['Review_Text']}")
                st.write(f"Date: {review['Date_and_Time'].strftime('%Y-%m-%d %H:%M:%S')}")
                st.write("---")

        # Neutral Reviews Tab
        with tabs[1]:
            st.write(f"Neutral Reviews ({len(neutral_reviews)})")
            for review in neutral_reviews:
                st.write(f"Reviewer: {review['Reviewer_Name']}")
                st.write(f"Review: {review['Review_Text']}")
                st.write(f"Date: {review['Date_and_Time'].strftime('%Y-%m-%d %H:%M:%S')}")
                st.write("---")

        # Negative Reviews Tab
        with tabs[2]:
            st.write(f"Negative Reviews ({len(negative_reviews)})")
            for review in negative_reviews:
                st.write(f"Reviewer: {review['Reviewer_Name']}")
                st.write(f"Review: {review['Review_Text']}")
                st.write(f"Date: {review['Date_and_Time'].strftime('%Y-%m-%d %H:%M:%S')}")
                st.write("---")