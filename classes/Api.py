# -*- coding: utf-8 -*-

#################################################
# Api.py     		
# 22 July 2013
# Said ÖZCAN									
# Instagram Printer
#################################################

import httplib, urllib2, json, time, sys, shutil, os, Printer, stat, re, datetime, yaml


class Api:

	# Instagram Api Url
	apiUrl = 'api.instagram.com'


	# Instagram Api Access Token
	accessToken = '209007001.32dc0e6.fa922df8ffbb4cba90529aab1a45e3d9'


	# Hashtag to search
	searchHashtag = 'InstagramPrinter'


	#Api connection delay time
	delayTime = 30


	#Html file page title
	pageTitle = 'InstagramPrinter'


	# Instagram Api Method Type
	method = 'GET'


	#Instagram Api path
	apiPath = '/v1/tags/{$hashTag}/media/recent?access_token={$accessToken}'


	#Api connection flag
	#if methods below can't finish it's job within delay time, this flag will prevent send second request
	apiConnectionFlag = 0


	#Output directory
	outputDirectory = 'outputs/'

	

	##################
	# method __init__
	# the __init__ method
	# @param self
	# @return void
	##################

	def __init__(self):

		print '>>InstagramPrinter: Initializing'

		self.get_configurations()

		if self.searchHashtag is None:

			print '>>InstagramPrinter: Missing argument: hashtag'

			sys.exit(0)

		if self.accessToken is None:

			print '>>InstagramPrinter: Missing argument: access token'

			sys.exit(0)

		
		#replacing hashtag with the reserved string
		self.apiPath = self.apiPath.replace( '{$hashTag}' , self.searchHashtag  )


		#replacing access token with the reserved string
		self.apiPath = self.apiPath.replace( '{$accessToken}' , self.accessToken )

		if True is self.check_network():

			while 1:

				while self.apiConnectionFlag is 1:
					pass

				self.connect_to_api()

				print '>>InstagramPrinter: Application will sleep for ' + str(self.delayTime) + ' seconds.'
				
				time.sleep( float(self.delayTime) )
		else:

			print '>>InstagramPrinter: No network connection'


	##################
	# method connect_to_api
	# this method connects to instagram api
	# @param self
	# @return void
	##################

	def connect_to_api(self):

		print '>>InstagramPrinter: Connecting To Api'
		
		self.apiConnectionFlag = 1
		#check network connection
		try:
		
			httpsObject = httplib.HTTPSConnection( self.apiUrl )
			
			httpsObject.request(self.method, self.apiPath)

			response = httpsObject.getresponse()			
			
			if not response.status is 200:

				print '>>InstagramPrinter: HTTP Response Code is not 200'

				pass

			else:

				responseJson = response.read()

				self.process_data( responseJson )

		except Exception as exc:

			print '>>InstagramPrinter: An Exception Raised During Connecting To Api:' + str(exc)

			sys.exit(0)


	##################
	# method process_data
	# this method handles json object and creates semantic data
	# @param self
	# @return void
	##################

	def process_data( self, responseJson ):
		
		print '>>InstagramPrinter: Processing Data'		
		
		try:

			response = json.loads( responseJson )

			data = response['data']

			if len(data):

				for d in data:
					
					self.save_data_as_html( d )

			else: 
				
				print '>>InstagramPrinter: No photos fetched'

		except Exception as exc:
			
			print '>>InstagramPrinter: An Exception Raised During process_data:' + str(exc)

			sys.exit(0)
	

	##################
	# method process_data
	# this method saves data as html
	# @param self
	# @return void
	##################

	def save_data_as_html(self, data):
		
		print '>>InstagramPrinter: Will Generate HTML if not exists before'	

		self.apiConnectionFlag = 0

		fileName = str(data['created_time']) + '.html'

		source = self.outputDirectory + 'templates/main.html'
		
		destination = self.outputDirectory + 'views/#' + self.searchHashtag + '/'

		if not os.path.exists( destination ):
			os.makedirs( destination )
			os.chmod( destination, 0777)
		
		#user data
		user = data['user']

		#comments
		comments = data['comments']

		#likes
		likes = data['likes']

		#image array for standart resolution
		standartResolutionImage =  data['images']['standard_resolution']
		
		if True == os.path.exists( destination + fileName):
			print '>>InstagramPrinter: File ' + fileName + ' already exists. Will pass this time.'		
			return 
		else:
		
			try:
				
				with open( source ) as file:

					template = file.read()

			except Exception as exc:

				print '>>InstagramPrinter: An Exception Raised During generating view:' + str(exc)

				sys.exit(0)
			
			
			template = template.replace( '{$title}', self.pageTitle )

			template = template.replace( '{$postOwner}', user['username'])

			template = template.replace( '{$postOwnerAvatar}', user['profile_picture'])

			template = template.replace( '{$postDate}', datetime.datetime.fromtimestamp(int(data['created_time'])).strftime('%d %B %Y, %H:%M'))

			template = template.replace( '{$photoUrl}', standartResolutionImage['url'] )

			template = template.replace( '{$photoWidth}', str(standartResolutionImage['width']) )

			template = template.replace( '{$photoHeight}', str(standartResolutionImage['height']) )

			likeCount = len(likes['data'])

			if likeCount > 0:

				if likeCount > 2:
					
					likeSentence = likes['data'][0]['username'] + ', ' +  likes['data'][1]['username'] + ' ve ' + str(likeCount-2) + ' kisi begendi.'

				elif likeCount is 2:

					likeSentence = likes['data'][0]['username'] + ', ' +  likes['data'][1]['username'] + ' begendi.'

				else:

					likeSentence = likes['data'][0]['username'] + ' begendi.'

			else:
				
				likeSentence = 'Henuz kimse begenmedi'
				

			template = template.replace( '{$likes}', likeSentence )

			startOfComments = template.index( '{$comments}' ) + len( '{$comments}' )

			endOfComments = template.index( '{/$comments}', startOfComments )

			commentsBlockWithData = ''

			if comments['count'] > 0:
				
				for comment in comments['data']:
					
					commentsBlock = template[startOfComments:endOfComments]

					commentsBlock = commentsBlock.replace( '{$commentOwner}', comment['from']['username'] )

					commentsBlock = commentsBlock.replace( '{$commentOwnerAvatar}', comment['from']['profile_picture'] )

					commentsBlock = commentsBlock.replace( '{$commentText}', comment['text'] )
					
					commentsBlockWithData += commentsBlock

				template = template.replace( '{$comments}' + template[startOfComments:endOfComments] + '{/$comments}', commentsBlockWithData )

			else:
			
				template = template.replace( '{$comments}' + template[startOfComments:endOfComments] + '{/$comments}', 'Yorum yapilmadi.' )
				
			

			newFilePath = destination + data['created_time'] + '.html'
			
			if True == os.path.exists(newFilePath):
				os.remove(newFilePath)
			
			newFile = open( newFilePath, 'w+' )

			newFile.write(template)

			newFile.close()

			print '>>InstagramPrinter: ' + data['created_time'] + '.html has been generated.' 

	##################
	# method check_network
	# this method checks network connection
	# @param self
	# @return void
	##################

	def check_network(self):

		try:

			response=urllib2.urlopen('http://google.com',timeout=1)

			return True

		except:
			return False

	##################
	# method get_configurations
	# this method gets the configurations of application from config.yaml
	# @param self
	# @return void
	##################
	def get_configurations(self):		
		
		try:
		
			configurations = open('config.yaml')
		
			data = yaml.safe_load(configurations)

			self.accessToken = data['accessToken']

			self.searchHashtag = data['searchHashtag']

			self.delayTime = data['delayTime']

			self.pageTitle = data['pageTitle']
			
			configurations.close()
		
		except Exception as exc:
			print '>>InstagramPrinter: Error setting configuration: ' + str(exc)