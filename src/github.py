import requests
import time
import os
from datetime import datetime, timedelta
import json
from pathlib import Path

class GitHubMonitor:
    def __init__(self, config_file="repo.ghicfg"):
        self.config_file = config_file
        self.cache_file = "monitor_cache.json"
        self.github_api = "https://api.github.com"
        self.headers = {
            "Accept": "application/vnd.github.v3+json"
        }
        
        # Add GitHub token if available
        github_token = os.getenv("GITHUB_TOKEN")
        if github_token:
            self.headers["Authorization"] = f"token {github_token}"
    
    def load_cache(self):
        """Load the last seen issues and PRs from cache file."""
        if Path(self.cache_file).exists():
            with open(self.cache_file, 'r') as f:
                return json.load(f)
        return {}
        
    def get_last_check_time(self, repo):
        """Get the last check time for a repository."""
        cache = self.load_cache()
        if repo in cache and "last_check" in cache[repo]:
            return cache[repo]["last_check"]
        return (datetime.utcnow() - timedelta(minutes=5)).isoformat() + "Z"
        
    def update_last_check_time(self, repo):
        """Update the last check time for a repository."""
        cache = self.load_cache()
        if repo not in cache:
            cache[repo] = {}
        cache[repo]["last_check"] = datetime.utcnow().isoformat() + "Z"
        self.save_cache(cache)

    def save_cache(self, cache):
        """Save the current state to cache file."""
        with open(self.cache_file, 'w') as f:
            json.dump(cache, f)

    def parse_config(self):
        """Parse the configuration file."""
        repos = {}
        with open(self.config_file, 'r') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#'):
                    repo, interval = line.split(':')
                    repos[repo] = int(interval)
        return repos

    def get_issues_and_prs(self, repo):
        """Fetch both issues and PRs for a repository."""
        issues_url = f"{self.github_api}/repos/{repo}/issues"
        params = {
            "state": "all",
            "sort": "created",
            "direction": "desc",
            "per_page": 10,  # Limit to latest 10 items
            "since": self.get_last_check_time(repo)  # Only get items since last check
        }
        
        try:
            response = requests.get(issues_url, headers=self.headers, params=params)
            response.raise_for_status()
            items = response.json()
            
            # Update last check time
            self.update_last_check_time(repo)
            
            return items
        except requests.exceptions.RequestException as e:
            print(f"Error fetching data for {repo}: {e}")
            return []

    def notify(self, repo, item_type, item):
        """Send desktop notification about new issue or PR."""
        from plyer import notification
        
        title = f"New {item_type} in {repo}"
        message = (
            f"Title: {item['title']}\n"
            f"Created by: {item['user']['login']}\n"
            f"URL: {item['html_url']}"
        )
        
        # Send desktop notification
        notification.notify(
            title=title,
            message=message,
            app_icon=None,  # Path to your icon file if needed
            timeout=10      # Notification will stay for 10 seconds
        )
        
        # Also log to console for reference
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        print(f"\n[{timestamp}] {title}")
        print(message)
        print("-" * 50)

    def monitor(self):
        """Main monitoring loop."""
        print("Starting GitHub repository monitor...")
        repos = self.parse_config()
        cache = self.load_cache()
        
        while True:
            for repo, interval in repos.items():
                # Initialize cache for new repositories
                if repo not in cache:
                    cache[repo] = {"latest_id": 0}
                
                items = self.get_issues_and_prs(repo)
                if items:
                    latest_id = cache[repo]["latest_id"]
                    
                    for item in items:
                        item_id = item["id"]
                        if item_id > latest_id:
                            item_type = "Pull Request" if "pull_request" in item else "Issue"
                            self.notify(repo, item_type, item)
                            cache[repo]["latest_id"] = max(latest_id, item_id)
                
                # Save cache after checking each repository
                self.save_cache(cache)
                
                # Wait for the specified interval
                time.sleep(interval)

def main():
    monitor = GitHubMonitor()
    try:
        monitor.monitor()
    except Exception as e:
        print(f"An error occurred: {e}")
