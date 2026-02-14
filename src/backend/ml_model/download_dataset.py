import pandas as pd
import requests

def download_phishing_dataset():
    """
    Download phishing URL dataset from GitHub
    """
    # Phishing URLs
    phishing_url = "https://raw.githubusercontent.com/faizann24/Using-machine-learning-to-detect-malicious-URLs/master/data/data.csv"
    
    print("Downloading dataset...")
    df = pd.read_csv(phishing_url)
    
    # Save to local file
    df.to_csv('ml_model/url_dataset.csv', index=False)
    print(f" Dataset downloaded: {len(df)} URLs")
    print(f"Columns: {df.columns.tolist()}")
    
    return df

if __name__ == "__main__":
    download_phishing_dataset()