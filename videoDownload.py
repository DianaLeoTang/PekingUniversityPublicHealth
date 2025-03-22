import time
import os
import re
import json
import argparse
import requests
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
import logging

class VideoDownloader:
    def __init__(self, download_dir="downloads", headless=False):
        self.download_dir = download_dir
        self.headless = headless
        self.setup_logging()
        self.setup_browser()
        
    def setup_logging(self):
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[logging.StreamHandler()]
        )
        self.logger = logging.getLogger("VideoDownloader")
        
    def setup_browser(self):
        # Create downloads directory if it doesn't exist
        os.makedirs(self.download_dir, exist_ok=True)
        
        # Configure Chrome options
        chrome_options = Options()
        if self.headless:
            chrome_options.add_argument("--headless")
        chrome_options.add_argument("--disable-gpu")
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--window-size=1920,1080")
        
        # Important for video elements
        chrome_options.add_argument("--autoplay-policy=no-user-gesture-required")
        chrome_options.add_experimental_option("prefs", {
            "download.default_directory": os.path.abspath(self.download_dir),
            "download.prompt_for_download": False,
            "download.directory_upgrade": True,
            "safebrowsing.enabled": True
        })
        
        # Setup Chrome WebDriver
        service = Service(ChromeDriverManager().install())
        self.driver = webdriver.Chrome(service=service, options=chrome_options)
        self.logger.info("Browser setup complete")
        
    def navigate_to_url(self, url):
        """Navigate to the specified URL"""
        self.logger.info(f"Navigating to {url}")
        self.driver.get(url)
        self.logger.info(f"Page loaded: {self.driver.title}")
        # Wait for the page to load properly
        time.sleep(5)
        
    def extract_video_sources(self):
        """Extract all video sources from the page"""
        self.logger.info("Extracting video sources")
        video_sources = []
        
        # Find all video elements
        video_elements = self.driver.find_elements(By.TAG_NAME, "video")
        self.logger.info(f"Found {len(video_elements)} video elements")
        
        for idx, video in enumerate(video_elements):
            try:
                # Get the direct src attribute
                src = video.get_attribute('src')
                
                # If no direct src, look for source elements
                if not src:
                    source_elements = video.find_elements(By.TAG_NAME, 'source')
                    for source in source_elements:
                        src = source.get_attribute('src')
                        if src:
                            break
                
                # Also check for data attributes that might contain video URLs
                if not src:
                    data_src = video.get_attribute('data-src')
                    if data_src:
                        src = data_src
                
                # Process blob URLs if found
                if src and src.startswith('blob:'):
                    self.logger.info(f"Found blob URL: {src}")
                    blob_info = {
                        'element_idx': idx,
                        'blob_url': src,
                        'type': 'blob'
                    }
                    video_sources.append(blob_info)
                elif src:
                    self.logger.info(f"Found direct URL: {src}")
                    video_sources.append({
                        'element_idx': idx,
                        'url': src,
                        'type': 'direct'
                    })
            except Exception as e:
                self.logger.error(f"Error extracting source from video element {idx}: {str(e)}")
                
        return video_sources

    def extract_from_network_requests(self):
        """Extract video sources from network requests"""
        self.logger.info("Extracting video from network requests")
        
        # Get performance logs
        performance_logs = self.driver.execute_script("""
            var performance = window.performance || window.mozPerformance || window.msPerformance || window.webkitPerformance || {};
            return performance.getEntries() || [];
        """)
        
        # Filter for potential video files
        video_extensions = ['.mp4', '.webm', '.m3u8', '.ts', '.m4s']
        video_urls = []
        
        for entry in performance_logs:
            try:
                if 'name' in entry:
                    url = entry['name']
                    # Check if URL might be a video file
                    if any(ext in url.lower() for ext in video_extensions) or 'video' in url.lower():
                        self.logger.info(f"Found potential video URL in network requests: {url}")
                        video_urls.append({
                            'url': url,
                            'type': 'network',
                            'contentType': entry.get('initiatorType', 'unknown')
                        })
            except Exception as e:
                self.logger.error(f"Error processing network entry: {str(e)}")
                
        return video_urls
        
    def extract_from_browser_cache(self):
        """Extract video URLs from browser cache"""
        self.logger.info("Attempting to extract from browser cache")
        
        # Execute JavaScript to get cached resources
        cache_entries = self.driver.execute_script("""
            var cacheData = [];
            try {
                var performance = window.performance || window.mozPerformance || window.msPerformance || window.webkitPerformance || {};
                var entries = performance.getEntriesByType('resource');
                for (var i = 0; i < entries.length; i++) {
                    if (entries[i].initiatorType === 'video' || 
                        entries[i].name.indexOf('.mp4') > -1 || 
                        entries[i].name.indexOf('.webm') > -1 ||
                        entries[i].name.indexOf('.m3u8') > -1 ||
                        entries[i].name.indexOf('.ts') > -1 ||
                        entries[i].name.indexOf('video') > -1) {
                        cacheData.push({
                            url: entries[i].name,
                            type: entries[i].initiatorType,
                            duration: entries[i].duration,
                            size: entries[i].encodedBodySize || entries[i].transferSize || 0
                        });
                    }
                }
            } catch (e) {
                console.error("Error accessing cache:", e);
            }
            return cacheData;
        """)
        
        if cache_entries:
            self.logger.info(f"Found {len(cache_entries)} potential video entries in cache")
            
            # Sort by size (largest are most likely to be videos)
            cache_entries.sort(key=lambda x: x.get('size', 0), reverse=True)
            
            for entry in cache_entries[:5]:  # Log top 5 entries by size
                self.logger.info(f"Cache entry: {entry}")
                
        return cache_entries
    
    def download_direct_video(self, url, filename):
        """Download video from a direct URL"""
        try:
            self.logger.info(f"Downloading from direct URL: {url}")
            
            # Set headers to mimic browser request
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
                'Referer': self.driver.current_url
            }
            
            # Stream the response to handle large files
            response = requests.get(url, headers=headers, stream=True)
            if response.status_code == 200:
                file_path = os.path.join(self.download_dir, filename)
                
                # Get content size if available
                file_size = int(response.headers.get('content-length', 0))
                if file_size > 0:
                    self.logger.info(f"File size: {file_size / (1024 * 1024):.2f} MB")
                
                # Download the file in chunks
                downloaded = 0
                with open(file_path, 'wb') as f:
                    for chunk in response.iter_content(chunk_size=8192):
                        if chunk:
                            f.write(chunk)
                            downloaded += len(chunk)
                            # Log progress for large files
                            if file_size > 0 and downloaded % (1024 * 1024) < 8192:  # Log roughly every MB
                                progress = (downloaded / file_size) * 100
                                self.logger.info(f"Download progress: {progress:.1f}%")
                
                self.logger.info(f"Download complete: {file_path}")
                return file_path
            else:
                self.logger.error(f"Failed to download video. Status code: {response.status_code}")
                return None
        except Exception as e:
            self.logger.error(f"Error downloading video: {str(e)}")
            return None
    
    def download_blob_video(self, video_info):
        """Download video from a blob URL by converting it via JavaScript"""
        self.logger.info(f"Attempting to download blob URL: {video_info['blob_url']}")
        
        try:
            # Find the video element
            video_elements = self.driver.find_elements(By.TAG_NAME, "video")
            if video_info['element_idx'] >= len(video_elements):
                self.logger.error("Video element no longer found on page")
                return None
                
            video_element = video_elements[video_info['element_idx']]
            
            # Play the video to ensure it's loaded
            self.driver.execute_script("arguments[0].play();", video_element)
            time.sleep(2)  # Allow video to start playing
            
            # Extract video information
            video_info = self.driver.execute_script("""
                var video = arguments[0];
                return {
                    duration: video.duration,
                    currentSrc: video.currentSrc,
                    videoWidth: video.videoWidth,
                    videoHeight: video.videoHeight
                };
            """, video_element)
            
            self.logger.info(f"Video info: {video_info}")
            
            # Create a temporary download function in the page
            download_script = """
            async function downloadBlobVideo(videoElement) {
                try {
                    // Get current source
                    const src = videoElement.src || videoElement.currentSrc;
                    if (!src) {
                        return { success: false, error: 'No video source found' };
                    }
                    
                    // Fetch the video data
                    const response = await fetch(src);
                    if (!response.ok) {
                        return { success: false, error: `Failed to fetch: ${response.status}` };
                    }
                    
                    // Get the blob data
                    const blob = await response.blob();
                    
                    // Create temporary URL
                    const blobUrl = URL.createObjectURL(blob);
                    
                    // Create a link to trigger download
                    const a = document.createElement('a');
                    a.style.display = 'none';
                    a.href = blobUrl;
                    a.download = 'video_' + new Date().getTime() + '.mp4';
                    document.body.appendChild(a);
                    a.click();
                    
                    // Clean up
                    setTimeout(() => {
                        document.body.removeChild(a);
                        URL.revokeObjectURL(blobUrl);
                    }, 100);
                    
                    return { success: true, filename: a.download, type: blob.type, size: blob.size };
                } catch (error) {
                    return { success: false, error: error.toString() };
                }
            }
            
            // Execute the function and return the result
            return downloadBlobVideo(arguments[0]);
            """
            
            result = self.driver.execute_script(download_script, video_element)
            self.logger.info(f"Download script result: {result}")
            
            if result.get('success'):
                self.logger.info(f"Video download triggered: {result.get('filename')}")
                
                # Wait for download to complete
                time.sleep(5)  # Give browser time to save the file
                
                # Check if file exists in download directory
                expected_file = os.path.join(self.download_dir, result.get('filename'))
                if os.path.exists(expected_file):
                    self.logger.info(f"Download confirmed: {expected_file}")
                    return expected_file
                else:
                    self.logger.warning(f"File not found in downloads directory: {expected_file}")
                    return None
            else:
                self.logger.error(f"Failed to download blob: {result.get('error')}")
                return None
        except Exception as e:
            self.logger.error(f"Error in download_blob_video: {str(e)}")
            return None
            
    def download_videos_from_page(self, url):
        """Main method to download videos from a page"""
        try:
            self.logger.info(f"Starting video extraction from {url}")
            self.navigate_to_url(url)
            
            # Extract video sources
            video_sources = self.extract_video_sources()
            network_videos = self.extract_from_network_requests()
            cache_videos = self.extract_from_browser_cache()
            
            # Combine all sources (removing duplicates)
            all_sources = video_sources + network_videos + cache_videos
            
            # If no videos found, return empty list
            if not all_sources:
                self.logger.warning("No videos found on the page")
                return []
                
            # Download videos
            downloaded_files = []
            
            # Process direct URLs first
            direct_sources = [s for s in all_sources if s.get('type') == 'direct']
            for idx, source in enumerate(direct_sources):
                if 'url' in source:
                    filename = f"direct_video_{idx}_{int(time.time())}.mp4"
                    file_path = self.download_direct_video(source['url'], filename)
                    if file_path:
                        downloaded_files.append(file_path)
            
            # Process blob URLs
            blob_sources = [s for s in all_sources if s.get('type') == 'blob']
            for source in blob_sources:
                file_path = self.download_blob_video(source)
                if file_path:
                    downloaded_files.append(file_path)
            
            # Process network sources (if not already downloaded)
            if not downloaded_files:
                network_sources = [s for s in all_sources if s.get('type') == 'network']
                for idx, source in enumerate(network_sources):
                    if 'url' in source:
                        filename = f"network_video_{idx}_{int(time.time())}.mp4"
                        file_path = self.download_direct_video(source['url'], filename)
                        if file_path:
                            downloaded_files.append(file_path)
            
            self.logger.info(f"Download complete. {len(downloaded_files)} files downloaded.")
            return downloaded_files
            
        except Exception as e:
            self.logger.error(f"Error in download_videos_from_page: {str(e)}")
            return []
            
    def close(self):
        """Close the browser and clean up"""
        self.logger.info("Closing browser")
        if self.driver:
            self.driver.quit()


def main():
    parser = argparse.ArgumentParser(description='Download videos from web pages')
    parser.add_argument('url', help='URL of the web page containing videos')
    parser.add_argument('--output', '-o', default='downloads', help='Output directory for downloaded videos')
    parser.add_argument('--headless', action='store_true', help='Run in headless mode')
    
    args = parser.parse_args()
    
    downloader = VideoDownloader(download_dir=args.output, headless=args.headless)
    try:
        downloaded_files = downloader.download_videos_from_page(args.url)
        if downloaded_files:
            print(f"Successfully downloaded {len(downloaded_files)} videos:")
            for file in downloaded_files:
                print(f" - {file}")
        else:
            print("No videos were downloaded.")
    finally:
        downloader.close()


if __name__ == "__main__":
    main()