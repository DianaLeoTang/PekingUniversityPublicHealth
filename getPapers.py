'''
Author: Diana Tang
Date: 2025-02-19 09:59:53
LastEditors: Diana Tang
Description: 用爬虫技术抓取某位作者的相关文章
FilePath: /PekingUniversityCode/PekingUniversityPublicHealth/getPapers.py
'''
import requests
from bs4 import BeautifulSoup
import time
import os

# 搜索作者的文章
def search_articles(author_name):
    url = f"https://scholar.google.com/scholar?q={author_name}"
    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'}
    
    response = requests.get(url, headers=headers)
    if response.status_code != 200:
        print("Error: Failed to retrieve Google Scholar page.")
        return []

    soup = BeautifulSoup(response.text, 'html.parser')
    articles = []
    for item in soup.find_all('h3', {'class': 'gs_rt'}):
        link = item.find('a')
        if link:
            articles.append(link.get('href'))
    return articles

# 下载文献
def download_articles(articles):
    if not os.path.exists("downloads"):
        os.mkdir("downloads")

    for idx, article_url in enumerate(articles, 1):
        try:
            response = requests.get(article_url, stream=True)
            if response.status_code == 200:
                filename = f"downloads/article_{idx}.pdf"
                with open(filename, 'wb') as f:
                    for chunk in response.iter_content(chunk_size=128):
                        f.write(chunk)
                print(f"Downloaded: {filename}")
            else:
                print(f"Failed to download article: {article_url}")
            time.sleep(1)  # Avoid getting blocked by Google
        except Exception as e:
            print(f"Error downloading {article_url}: {e}")

# 主程序
def main():
    author_name = input("Enter the author's name: ")
    articles = search_articles(author_name)
    if articles:
        print(f"Found {len(articles)} articles.")
        download_articles(articles)
    else:
        print("No articles found.")

if __name__ == "__main__":
    main()
