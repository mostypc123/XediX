# GitHub Integration Guide

## Overview
XediX's GitHub integration allows you to sync with GitHub repositories. This guide covers setup, configuration, and best practices.

## Prerequisites
- Basic understanding of GitHub repositories
- (Optional) GitHub Personal Access Token

## Configuration Steps

### 1. Basic Setup
Create or edit `repo.ghicfg` in your XediX installation directory. Each line follows this format:
```
owner/repository:update_interval
```

Example:
```
mostypc123/XediX:600
octocat/Hello-World:1200
```

### 2. Configuration Parameters
| Parameter | Description | Recommendation |
|-----------|-------------|----------------|
| owner | Repository owner username | Must match exactly |
| repository | Repository name | Must match case-sensitive name |
| update_interval | Seconds between API calls | Minimum 600 (10 minutes) |

### 3. API Authentication (Optional)

#### Windows
```cmd
setx GITHUB_TOKEN "your_personal_access_token"
```

#### Linux/macOS
```bash
echo 'export GITHUB_TOKEN="your_personal_access_token"' >> ~/.bashrc
source ~/.bashrc
```

## Rate Limits & Best Practices

### API Limits
- Unauthenticated: 60 requests/hour
- Authenticated: 5,000 requests/hour
- Calculate your needs: `(3600 / update_interval) * number_of_repos`

### Security
- Store tokens securely using environment variables
- Never commit tokens to version control
- Use tokens with minimal required permissions
- Regularly rotate authentication tokens

### Performance
- Use longer update intervals for stable repositories
- Consider caching frequently accessed data
- Monitor API usage through GitHub's dashboard

## Troubleshooting

### Common Issues
1. Rate limit exceeded
   - Increase update interval
   - Authenticate with API token
   - Reduce number of monitored repositories

2. Authentication failures
   - Verify token hasn't expired
   - Check environment variable is set correctly
   - Ensure token has required permissions

3. Repository not found
   - Verify repository name and case
   - Check access permissions
   - Confirm repository still exists

## Disclaimer
Users are responsible for:
- Managing their API usage
- Securing their authentication tokens
- Complying with GitHub's policies

---
layout: default
---