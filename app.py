import streamlit as st
import requests
from datetime import datetime, timedelta
from deep_translator import GoogleTranslator
import time
import nltk
from nltk.sentiment.vader import SentimentIntensityAnalyzer

# Download NLTK resources (if not already downloaded)


def download_vader_lexicon():
    try:
        nltk.data.find('vader_lexicon')
    except LookupError:
        nltk.download('vader_lexicon')

# Check if vader_lexicon is downloaded, if not download it
download_vader_lexicon()

st.markdown("""
<style>
    .custom-text-area {
        max-width: 1000px; /* Adjust the maximum width as needed */
        width: 150%; /* Ensure it takes full available width */
        height: 100px; /* Let the height adjust dynamically based on content */
        overflow: auto; /* Add scrollbar if content exceeds height */
    }
</style>
""", unsafe_allow_html=True)

# Define your API keys
NEWS_APIKEY = 'bf2e8b28eae641fe9c1356d9b9c3f1f3'

# Initialize Streamlit app
st.title('Stock News Sentiment Analysis')

websites = ['moneycontrol.com', 
            'etmarket.com', 
            'economictimes.indiatimes.com',
            'timesofindia.indiatimes.com',
            'capitalmarket.com',
            'livemint.com',
            'finance.yahoo.com',
            'bloomberg.com',
            'cnbc.com',
            'investopedia.com',
            'business-standard.com']

def fetch_stock_news(stock_name, domains=websites):
    try:
        # Construct the URL with parameters
        url = 'https://newsapi.org/v2/everything'
        
        # Calculate dates for the date range (from today to last one week)
        today = datetime.today().strftime('%Y-%m-%d')
        last_week = (datetime.today() - timedelta(days=7)).strftime('%Y-%m-%d')
        
        params = {
            'q': f"{stock_name} AND (stocks OR market OR finance OR trading)",
            'domains': ','.join(domains),  # Comma-separated list of domains
            'apiKey': NEWS_APIKEY,
            'from': last_week,  # From last one week ago
            'to': today,  # To today's date
            'sortBy': 'publishedAt'  # Sort by publishedAt
        }
        
        # Make the GET request with parameters
        response = requests.get(url, params=params)
        
        # Check if request was successful (status code 200)
        if response.status_code == 200:
            return response.json()['articles']
        else:
            st.error(f"Failed to fetch news. Status code: {response.status_code}")
            return None
    except requests.exceptions.RequestException as e:
        st.error(f"Error fetching news: {e}")
        return None

def get_last_week_date():
    today = datetime.today()
    last_week = today - timedelta(days=7)
    return last_week.strftime('%Y-%m-%d')

def analyze_sentiment(text):
    sia = SentimentIntensityAnalyzer()
    sentiment_score = sia.polarity_scores(text)['compound']
    if sentiment_score > 0.05:
        return 'Positive'
    elif sentiment_score < -0.05:
        return 'Negative'
    else:
        return 'Neutral'

def translate_to_english(text):
    max_retries = 3
    retries = 0
    while retries < max_retries:
        try:
            translation = GoogleTranslator(source='auto', target='en').translate(text)
            return translation
        except Exception as e:
            st.warning(f"Translation attempt failed. Retrying... ({retries+1}/{max_retries})")
            time.sleep(1)  # Wait before retrying
            retries += 1
    st.error(f"Failed to translate: {text}")
    return text  # Return original text if all retries fail

# Streamlit UI components
def main():
    stock_name = st.text_input('Enter Stock Name (e.g., TATAMOTORS for Tata Motors)')
    submit_button = st.button('Fetch News and Analyze Sentiment')

    if submit_button:
        if not stock_name.strip():
            st.warning("Please enter a valid stock name.")
            return
        
        st.write(f"Fetching news for {stock_name} from selected websites...")
        news_articles = fetch_stock_news(stock_name)
        news_articles = sorted(news_articles, key=lambda x: x['publishedAt'], reverse=True)
        
        if news_articles:
            st.write(f"### Latest News for {stock_name} from Different Sources")
            count = 0
            for article in news_articles:
                # Check if the stock name is mentioned in the title or description
                if stock_name.lower() in article['title'].lower() or stock_name.lower() in article['description'].lower():
                    count += 1
                    translated_title = translate_to_english(article['title'])
                    translated_description = translate_to_english(article['description'])
                    translated_content = translate_to_english(article['content'])
                    
                    st.write(f"### {stock_name} News-{count}")
                    st.write(f"- **Title:**")
                    st.markdown(f"<textarea class='custom-text-area' disabled>{translated_title}</textarea>", unsafe_allow_html=True)
                    st.write(f"- **Description:**")
                    st.markdown(f"<textarea class='custom-text-area' disabled>{translated_description}</textarea>", unsafe_allow_html=True)
                    st.write(f"- **Content:**")
                    st.markdown(f"<textarea class='custom-text-area' disabled>{translated_content}</textarea>", unsafe_allow_html=True)
                    st.write(f"  **Published At:** {article['publishedAt']}")
                    st.write(f"  **Source:** {article['source']['name']}")
                    sentiment = analyze_sentiment(translated_description)
                    if sentiment:
                        st.write(f"  **Sentiment:** {sentiment}")
                        if sentiment == 'Positive':
                            st.write("  **Analysis:** Bullish")
                        elif sentiment == 'Negative':
                            st.write("  **Analysis:** Bearish")
                        else:
                            st.write("  **Analysis:** Neutral")
                    st.write('---')
            
            if count == 0:
                st.error(f"No news found for {stock_name} in the past week.")
                    
        else:
            st.error(f"Failed to fetch news for {stock_name} from selected websites. Please try again.")

if __name__ == '__main__':
    main()
