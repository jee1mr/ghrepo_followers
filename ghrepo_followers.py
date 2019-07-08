# -*- coding: utf-8 -*-

from github import Github, GithubException
from tinydb import TinyDB, Query
import pandas as pd
import requests
import requests_cache
import sys
import time
import click

class GithubRepo():
	"""
	For a given repository, fetch user information of
	all those who starred, watching, or forked the repository.

	Fetch Username, Name, Email, Website, Organization and Location
	and export to CSV.
	"""
	def __init__(self, url, access_token=None):
		requests_cache.install_cache('github_cache')
		self.url = url
		self.repo = None
		self.access_token = access_token
		self.g = Github(access_token)
		self.db = TinyDB('./db.json')
		try:
			self.repo = self.g.get_repo(self.__parse_repo_name_from_url(self.url))
		except GithubException as e:
			raise Exception('API rate limit exceeded. Please try again after ', self.__time_remaining(self.g.rate_limiting_resettime), 'minute(s)') 

	def get_all_users_info(self):
		"""
		Get user info for all starrers, watchers, forkers
		"""
		starrers = list(map(lambda user: self.__get_user_info(user), self.__get_starrers()))
		watchers = list(map(lambda user: self.__get_user_info(user), self.__get_watchers()))
		forkers = list(map(lambda user: self.__get_user_info(user), self.__get_forkers()))

		return starrers + watchers + forkers

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
				raise Exception('Github API Failed. Please check for rate limits.')
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
				raise Exception('Github API Failed. Please check for rate limits.')
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
				raise Exception('Github API Failed. Please check for rate limits.')
			res_per_page = r.json()
			if not res_per_page:
				break
			users_per_page = [user['login'] for user in res_per_page]
			users += users_per_page
			page += 1
		return users

	def __get_user_from_db(self, username):
		"""
		Fetch user details from tinydb if already exists,
		else return empty object
		"""
		try:
			table = self.db.table(self.repo.name)
			user = table.search(Query()['username'] == username)
			if len(user):
				return user[0]
		except Exception as e:
			print('Fetching from tinydb failed', e)
		return {}

	def __save_user_to_db(self, user):
		"""
		Save user details to tinydb
		"""
		try:
			table = self.db.table(self.repo.name)
			table.upsert(user, Query()['username'] == user['username'])
		except Exception as e:
			print('Saving to tinydb failed', e)

	def __get_user_info(self, username):
		"""
		Get user info for a given github username.
		Returns a dictionary of User details.
		:param str username:
		    The github username for which the details need
		    to be extracted.
		"""
		print('Fetching details for username: ', username)
		retry_limit = 3
		while retry_limit:
			try:
				user = self.__get_user_from_db(username)
				if user:
					break
				gh_user =  self.g.get_user(username)
				user = {'username': gh_user.login, 'name': gh_user.name, 'email': gh_user.email,
						'website': gh_user.blog, 'organization': gh_user.company, 'location': gh_user.location}
				self.__save_user_to_db(user)
				break
			except GithubException as e:
				raise Exception('API rate limit exceeded. Please try again after ', self.__time_remaining(self.g.rate_limiting_resettime), 'minute(s)')
			except Exception as e:
				print('Fetching user info failed', e)
				print('Retrying..')
			retry_limit -= 1

		return user

	def __time_remaining(self, epoch):
		current_epoch = time.time()
		if epoch > current_epoch:
			return int((epoch - time.time()) / 60)
		return 0

@click.command()
@click.option('--repo', help='Github repo link. Single or Multiple.', multiple=True, required=True)
@click.option('--access_token', default=None, help='Your personal github access token. Find instructions in the README. [optional]')
def get_all_users(repo, access_token):
	"""
		Example: 
		python ghrepo_followers.py --repo https://github.com/d6t/d6tpipe --repo https://github.com/d6t/d6tflow --access_token ACCESS_TOKEN
	"""
	users = []
	for _repo in repo:
		try:
			ghrepo = GithubRepo(_repo, access_token)
			users += ghrepo.get_all_users_info()
		except Exception as e:
			click.echo(click.style(str(e), fg='red'))
			sys.exit(1)

	df_users = pd.DataFrame(users)

	df_email_users = df_users[~df_users['email'].isna()]
	df_noemail_users = df_users[df_users['email'].isna()]

	df_email_users.to_csv('users-emails.csv', index=False)
	df_noemail_users.to_csv('users-noemails.csv', index=False)

if __name__ == '__main__':
	get_all_users()
	
