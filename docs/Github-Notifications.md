Here, you will learn how to use the Github Integration feature.

## Configuration
To start, open the `repo.ghicfg` file. If you do not have one, create one.
Set the value to:
```
user/repo:seconds_between reload
```
`user` - The owner of the repo<br>
`repo` - The name of the repo<br>
`seconds_between reload` - How much seconds between fetching repo data again<br>

**Please set `seconds_between reload` to at least 600, or you will probably reach the API usage limits.**<br>
**You can set as many repos as you want.**

If you want to use your Github API Token, _you might reach API rate limits_, run:
```cmd
# Widnows
setx GITHUB_TOKEN "your_token"
```
```bash
# Linux / Unix / macOS
export GITHUB_TOKEN=value
source ~/.bashrc
```

## Disclaimer
* I'm not responsible for you reaching API limits.
* If you reach an API rate limit on your API key, I'm not responsible for anything happening.