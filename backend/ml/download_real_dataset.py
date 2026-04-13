import pandas as pd
import requests
import os
import tarfile
import email
from email import policy
from email.parser import BytesParser
import re
from io import BytesIO
import random

def download_spam_assassin_dataset():
    """
    Download SpamAssassin Public Corpus
    Contains spam and ham (legitimate) emails
    """
    print(" Downloading SpamAssassin dataset...")
    
    datasets = {
        'spam': [
            'https://spamassassin.apache.org/old/publiccorpus/20030228_spam.tar.bz2',
            'https://spamassassin.apache.org/old/publiccorpus/20030228_spam_2.tar.bz2'
        ],
        'ham': [
            'https://spamassassin.apache.org/old/publiccorpus/20030228_easy_ham.tar.bz2',
            'https://spamassassin.apache.org/old/publiccorpus/20030228_easy_ham_2.tar.bz2',
            'https://spamassassin.apache.org/old/publiccorpus/20030228_hard_ham.tar.bz2'
        ]
    }
    
    emails_data = []
    
    # Download and parse spam emails
    print("\n Processing spam emails...")
    for idx, url in enumerate(datasets['spam']):
        try:
            print(f"  Downloading {url.split('/')[-1]}...")
            response = requests.get(url, timeout=30)
            
            if response.status_code == 200:
                # Extract tar.bz2 file
                tar = tarfile.open(fileobj=BytesIO(response.content), mode='r:bz2')
                
                count = 0
                for member in tar.getmembers():
                    if member.isfile():
                        f = tar.extractfile(member)
                        if f:
                            try:
                                email_content = f.read()
                                parsed_email = parse_email_content(email_content)
                                if parsed_email:
                                    parsed_email['label'] = 1  # Spam/Phishing
                                    emails_data.append(parsed_email)
                                    count += 1
                                    if count % 100 == 0:
                                        print(f"    Processed {count} spam emails...", end='\r')
                            except:
                                pass
                
                print(f"     Processed {count} spam emails from {url.split('/')[-1]}")
                tar.close()
            else:
                print(f"     Failed to download: {url}")
        except Exception as e:
            print(f"     Error downloading {url}: {e}")
    
    # Download and parse ham (legitimate) emails
    print("\n Processing legitimate emails...")
    for idx, url in enumerate(datasets['ham']):
        try:
            print(f"  Downloading {url.split('/')[-1]}...")
            response = requests.get(url, timeout=30)
            
            if response.status_code == 200:
                tar = tarfile.open(fileobj=BytesIO(response.content), mode='r:bz2')
                
                count = 0
                for member in tar.getmembers():
                    if member.isfile():
                        f = tar.extractfile(member)
                        if f:
                            try:
                                email_content = f.read()
                                parsed_email = parse_email_content(email_content)
                                if parsed_email:
                                    parsed_email['label'] = 0  # Legitimate
                                    emails_data.append(parsed_email)
                                    count += 1
                                    if count % 100 == 0:
                                        print(f"    Processed {count} legitimate emails...", end='\r')
                            except:
                                pass
                
                print(f"     Processed {count} legitimate emails from {url.split('/')[-1]}")
                tar.close()
            else:
                print(f"     Failed to download: {url}")
        except Exception as e:
            print(f"     Error downloading {url}: {e}")
    
    return emails_data

def parse_email_content(email_bytes):
    """Parse raw email bytes into structured data"""
    try:
        msg = BytesParser(policy=policy.default).parsebytes(email_bytes)
        
        # Extract basic fields
        subject = str(msg.get('subject', ''))
        from_header = str(msg.get('from', ''))
        to_header = str(msg.get('to', ''))
        date = str(msg.get('date', ''))
        
        # Extract body
        body_plain = ''
        body_html = ''
        attachments = []
        
        if msg.is_multipart():
            for part in msg.walk():
                content_type = part.get_content_type()
                content_disposition = str(part.get("Content-Disposition", ""))
                
                if content_type == "text/plain" and "attachment" not in content_disposition:
                    try:
                        body_plain += part.get_payload(decode=True).decode('utf-8', errors='ignore')
                    except:
                        pass
                
                elif content_type == "text/html" and "attachment" not in content_disposition:
                    try:
                        body_html += part.get_payload(decode=True).decode('utf-8', errors='ignore')
                    except:
                        pass
                
                elif "attachment" in content_disposition:
                    filename = part.get_filename()
                    if filename:
                        attachments.append({
                            'filename': filename,
                            'content_type': content_type,
                            'size': len(part.get_payload(decode=True)) if part.get_payload() else 0
                        })
        else:
            try:
                body_plain = msg.get_payload(decode=True).decode('utf-8', errors='ignore')
            except:
                pass
        
        # Extract URLs
        urls = extract_urls(body_plain + " " + body_html)
        
        # Extract auth headers
        spf = str(msg.get('received-spf', ''))
        dkim = str(msg.get('dkim-signature', ''))
        dmarc = str(msg.get('authentication-results', ''))
        reply_to = str(msg.get('reply-to', ''))
        
        return {
            'subject': subject[:500],  # Limit length
            'from': from_header[:200],
            'to': to_header[:200],
            'date': date[:100],
            'body_plain': body_plain[:2000],  # Limit to first 2000 chars
            'body_html': body_html[:2000],
            'urls': str(urls[:20]),  # Limit to 20 URLs
            'attachments': str(attachments[:10]),  # Limit to 10 attachments
            'spf': spf[:100],
            'dkim': dkim[:100],
            'dmarc': dmarc[:100],
            'reply_to': reply_to[:200]
        }
    except Exception as e:
        return None

def extract_urls(text):
    """Extract URLs from text"""
    url_pattern = r'http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\\(\\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+'
    urls = re.findall(url_pattern, text)
    
    # Remove duplicates
    seen = set()
    unique_urls = []
    for url in urls:
        if url not in seen and len(url) < 200:
            seen.add(url)
            unique_urls.append(url)
    
    return unique_urls

def download_additional_phishing_samples():
    """
    Create additional synthetic phishing samples
    Based on common phishing patterns
    """
    print("\n Creating additional phishing samples...")
    
    phishing_templates = [
        {
            'subject': 'URGENT: Verify Your {brand} Account',
            'from': '{brand} Security <security@{brand}-verify.{tld}>',
            'body_plain': 'Your account has been locked due to unusual activity. Verify immediately: {url}',
            'urls': ['http://{brand}-secure-login.{fake_domain}'],
            'spf': 'fail',
            'label': 1
        },
        {
            'subject': 'Your {brand} payment failed',
            'from': 'Billing <noreply@{brand}.{tld}>',
            'body_plain': 'We could not process your payment. Update your information now: {url}',
            'urls': ['https://{brand}-billing-update.{fake_domain}'],
            'spf': 'softfail',
            'label': 1
        },
        {
            'subject': 'You have won ${amount}!',
            'from': 'Lottery Winner <winner@prize-claim.{tld}>',
            'body_plain': 'Congratulations! Claim your prize here: {url}',
            'urls': ['http://claim-prize-now.{fake_domain}'],
            'spf': 'fail',
            'label': 1
        },
        {
            'subject': 'Action Required: Confirm your identity',
            'from': '{brand} Support <support@{brand}-help.{tld}>',
            'body_plain': 'Click here to confirm: {url} or your account will be suspended.',
            'urls': ['http://{brand}-confirm.{fake_domain}'],
            'spf': 'fail',
            'label': 1
        },
        {
            'subject': 'Security Alert: Unusual login detected',
            'from': '{brand} <alert@{brand}-security.{tld}>',
            'body_plain': 'We detected a login from an unknown device. If this was not you, secure your account: {url}',
            'urls': ['https://{brand}-secure.{fake_domain}'],
            'spf': 'fail',
            'label': 1
        }
    ]
    
    brands = ['paypal', 'amazon', 'microsoft', 'apple', 'netflix', 'bank', 'ebay']
    fake_domains = ['tk', 'ml', 'ga', 'cf', 'xyz', 'online', 'site']
    tlds = ['com', 'net', 'org']
    
    synthetic_emails = []
    
    for _ in range(500):  # Generate 500 synthetic phishing emails
        template = random.choice(phishing_templates)
        brand = random.choice(brands)
        fake_domain = random.choice(fake_domains)
        tld = random.choice(tlds)
        amount = random.randint(100, 10000)
        
        email_data = {
            'subject': template['subject'].format(brand=brand, amount=amount),
            'from': template['from'].format(brand=brand, tld=tld),
            'to': 'user@example.com',
            'date': '2024-01-01 12:00:00',
            'body_plain': template['body_plain'].format(brand=brand, url=f'http://{brand}-verify.{fake_domain}'),
            'body_html': '',
            'urls': str([url.format(brand=brand, fake_domain=fake_domain) for url in template['urls']]),
            'attachments': '[]',
            'spf': template['spf'],
            'dkim': '',
            'dmarc': '',
            'reply_to': '',
            'label': template['label']
        }
        
        synthetic_emails.append(email_data)
    
    print(f"  Created {len(synthetic_emails)} synthetic phishing emails")
    
    return synthetic_emails

def create_real_email_dataset():
    """Main function to create comprehensive dataset"""
    
    print("=" * 70)
    print(" Creating Real Email Phishing Dataset")
    print("=" * 70)
    
    all_emails = []
    
    # Download SpamAssassin corpus
    spamassassin_emails = download_spam_assassin_dataset()
    all_emails.extend(spamassassin_emails)
    
    print(f"\n SpamAssassin emails: {len(spamassassin_emails)}")
    
    # Add synthetic phishing samples
    synthetic_emails = download_additional_phishing_samples()
    all_emails.extend(synthetic_emails)
    
    print(f" Synthetic phishing emails: {len(synthetic_emails)}")
    
    # Convert to DataFrame
    df = pd.DataFrame(all_emails)
    
    # Remove duplicates
    initial_count = len(df)
    df = df.drop_duplicates(subset=['subject', 'from'])
    removed = initial_count - len(df)
    
    if removed > 0:
        print(f"\n🧹 Removed {removed} duplicate emails")
    
    # Shuffle dataset
    df = df.sample(frac=1, random_state=42).reset_index(drop=True)
    
    # Save dataset
    os.makedirs('data', exist_ok=True)
    df.to_csv('data/email_dataset_real.csv', index=False, escapechar='\\', quoting=1)    
    # Print statistics
    print("\n" + "=" * 70)
    print("DATASET STATISTICS")
    print("=" * 70)
    print(f"Total emails: {len(df)}")
    print(f"  Legitimate (0): {(df['label'] == 0).sum()} ({(df['label'] == 0).sum() / len(df) * 100:.1f}%)")
    print(f"  Spam/Phishing (1): {(df['label'] == 1).sum()} ({(df['label'] == 1).sum() / len(df) * 100:.1f}%)")
    print(f"\n Saved to: data/email_dataset_real.csv")
    print("=" * 70)
    
    return df

if __name__ == "__main__":
    try:
        create_real_email_dataset()
    except Exception as e:
        print(f"\n Error: {e}")
        import traceback
        traceback.print_exc()