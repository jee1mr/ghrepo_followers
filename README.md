## ghrepo_followers

Find all users who starred, forked, watching your repo. Fetch their email, username, location
and other details into a CSV file.

You can also club multiple repos.

#### Usage:

```console
	$ python ghrepo_followers.py --repo https://github.com/<username>/<repo_name>/ --access_token <access_token>
```

For multiple repos:

```console
	$ python ghrepo_followers.py --repo https://github.com/<username>/<repo_name>/  --repo https://github.com/<username>/<repo_name>/ --access_token <access_token>
```
	
If you don't provide an access token, the requests will be made anonymously. But the API
rate limit would be 60 per hour. Whereas, for authenticated requests, the limit is 5000/hr.

Instructions for getting the access token 
[here](https://help.github.com/en/articles/creating-a-personal-access-token-for-the-command-line).

