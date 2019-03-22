# -*- coding: utf-8 -*-

from github import Github
import requests
import csv
import sys

class GithubRepo():
	"""
	For a given repository, fetch user information of
	all those who starred, watching, or forked the repository.

	Fetch Username, Name, Email, Website, Organization and Location.
	Export to CSV.

	Example Usage:
		ghrepo = GithubRepo('https://github.com/d6t/d6tpipe', 'your_github_access_token')
		starrers = ghrepo.get_starrers_user_info()
		ghrepo.export_to_csv(starrers)
		watchers = ghrepo.get_watchers_user_info()
		ghrepo.export_to_csv(watchers, filename='watchers.csv')
		forkers = ghrepo.get_forkers_user_info()
		ghrepo.export_to_csv(forkers, filename='forkers.csv')
	"""
	def __init__(self, url, access_token=None):
		self.url = url
		self.repo = None
		self.access_token = access_token
		self.g = Github(access_token)
		self.repo = self.g.get_repo(self.__parse_repo_name_from_url(self.url))

	def get_starrers_user_info(self):
		""" 
		Get user info for all the starrers
		"""
		starrers = self.__get_starrers()
		return list(map(lambda user: self.__get_user_info(user), starrers))

	def get_watchers_user_info(self):
		""" 
		Get user info for all the watchers
		"""
		watchers = self.__get_watchers()
		return list(map(lambda user: self.__get_user_info(user), watchers))

	def get_forkers_user_info(self):
		""" 
		Get user info for all the forkers
		"""
		forkers = self.__get_forkers()
		return list(map(lambda user: self.__get_user_info(user), forkers))

	def export_to_csv(self, users, filename='repo_followers.csv'):
		""" 
		Export user info data to CSV format
		"""
		if not len(users):
			return

		with open(filename, 'w+') as f:
			writer = csv.writer(f)
			writer.writerows([users[0].keys()])
			for user in users:
				user_row =[user[field] for field in user]
				writer.writerows([user_row])

	def __parse_repo_name_from_url(self, url):
		""" 
		The github library expects a repo_ower/repo_name format.
		Parse this information from the input repository URL.
		"""
		return url.replace('https://github.com/', '')

	def __get_starrers(self):
		"""
		Get all users who starred the repository.
		Returns a list of usernames.
		"""
		stargazers_count =  self.repo.stargazers_count
		page = 1
		users = []
		print('Number of starrers: ', stargazers_count)
		while len(users) < stargazers_count:
			r = requests.get(self.repo.stargazers_url, params={'page': page, 'access_token': self.access_token})
			if r.status_code != 200:
				raise('Github API Failed. Please check for rate limits.')
			res_per_page = r.json()
			if not res_per_page:
				break
			users_per_page = [user['login'] for user in res_per_page]
			users += users_per_page
			page += 1
		return users

	def __get_forkers(self):
		"""
		Get all users who forked the repository.
		Returns a list of usernames.
		"""
		forks_count =  self.repo.forks_count
		page = 1
		users = []
		print('Number of forkers: ', forks_count)
		while len(users) < forks_count:
			r = requests.get(self.repo.forks_url, params={'page': page, 'access_token': self.access_token})
			if r.status_code != 200:
				raise('Github API Failed. Please check for rate limits.')
			res_per_page = r.json()
			if not res_per_page:
				break
			users_per_page = [user['owner']['login'] for user in res_per_page]
			users += users_per_page
			page += 1
		return users

	def __get_watchers(self):
		"""
		Get all users who are watching the repository.
		Returns a list of usernames.
		"""
		subscribers_count =  self.repo.subscribers_count
		page = 1
		users = []
		print('Number of watchers: ', subscribers_count)
		while len(users) < subscribers_count:
			r = requests.get(self.repo.subscribers_url, params={'page': page, 'access_token': self.access_token})
			if r.status_code != 200:
				raise('Github API Failed. Please check for rate limits.')
			res_per_page = r.json()
			if not res_per_page:
				break
			users_per_page = [user['login'] for user in res_per_page]
			users += users_per_page
			page += 1
		return users

	def __get_user_info(self, username):
		"""
		Get user info for a given github username.
		Returns a dictionary of User details.
		:param str username:
		    The github username for which the details need
		    to be extracted.
		"""
		print('Fetching details for username: ', username)
		user = {}
		gh_user = self.g.get_user(username)
		user = {'username': gh_user.login, 'name': gh_user.name, 'email': gh_user.email,
				'website': gh_user.blog, 'organization': gh_user.company, 'location': gh_user.location}
		return user


if __name__ == '__main__':
	if len(sys.argv) < 2:
		print('Usage:  python ghrepo_followers.py https://github.com/<username>/<repo_name>/ <access_token>')
		sys.exit(1)
	ghrepo = GithubRepo(sys.argv[1], sys.argv[2])
	starrers = ghrepo.get_starrers_user_info()
	ghrepo.export_to_csv(starrers, filename='starrers.csv')
	watchers = ghrepo.get_watchers_user_info()
	ghrepo.export_to_csv(watchers, filename='watchers.csv')
	forkers = ghrepo.get_forkers_user_info()
	ghrepo.export_to_csv(forkers, filename='forkers.csv')

