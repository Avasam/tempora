# -*- coding: UTF-8 -*-

"""
tools.py:
  small functions or classes that don't have a home elsewhere
"""
#from __future__ import generators

import string, urllib

# DictMap is much like the built-in function map.  It takes a dictionary
#  and applys a function to the values of that dictionary, returning a
#  new dictionary with the mapped values in the original keys.
def DictMap( function, dictionary ):
	return dict( zip( dictionary.keys(), map( function, dictionary.values() ) ) )

# CoerceType takes a value and attempts to convert it to a float, long, or int.
#  If none of the conversions are successful, the original value is returned.
def CoerceType( value ):
	result = value
	for transform in ( float, long, int ):
		try: result = transform( value )
		except ValueError: pass

	return result

# Make a list into rows of nColumns columns.
# So if list = [1,2,3,4,5] and nColumns = 2, result is
#  [[1,3],[2,4],[5,None]].  If nColumns = 3, result is
#  [[1,3,5],[2,4,None]].
def makeRows( list, nColumns ):
	# calculate the minimum number of rows necessary to fit the list in n Columns
	nRows = len(list) / nColumns
	if len(list) % nColumns:
		nRows += 1
	# chunk the list into n Columns of length nRows
	result = chunkGenerator( list, nRows )
	# result is now a list of columns... transpose it to return a list of rows
	return map( None, *result )

# HTTP Query takes as an argument an HTTP query request (from the url after ?)
#  and maps all of the pairs in itself as a dictionary.
# So: HTTPQuery( 'a=b&c=3&4=20' ) == { 'a':'b', 'c':'3', '4':'20' }
class HTTPQuery( dict ):
	def __init__( self, query ):
		if not self.isValidQuery( query ):
			raise ValueError, 'Invalid query: %s' % query
		items = string.split( query, '&' )
		splitEqual = lambda s: string.split( s, '=' )
		itemPairs = map( splitEqual, items )
		unquoteSequence = lambda l: map( urllib.unquote, l )
		itemPairs = map( unquoteSequence, itemPairs )
		self.update( dict( itemPairs ) )

	def isValidQuery( self, query ):
		return query

	def __repr__( self ):
		itemPairs = self.items()
		quoteSequence = lambda l: map( urllib.quote, l )
		itemPairs = map( quoteSequence, itemPairs )
		joinEqual = lambda l: string.join( l, '=' )
		items = map( joinEqual, itemPairs )
		return string.join( items, '&' )

def chunkGenerator( seq, size ):
	for i in range( 0, len(seq), size ):
		yield seq[i:i+size]

import datetime

class QuickTimer( object ):
	def __init__( self ):
		self.Start()

	def Start( self ):
		self.startTime = datetime.datetime.now()

	def Stop( self ):
		return datetime.datetime.now() - self.startTime

import re, operator
# some code to do conversions from DMS to DD
class DMS( object ):
	dmsPatterns = [
		# This pattern matches the DMS string that assumes little formatting.
		#  The numbers are bunched together, and it is assumed that the minutes
		#  and seconds are two digits each.
		"""
		(-)?			# optional negative sign
		(?P<deg>\d+)	# number of degrees (saved as 'deg')
		(?P<min>\d{2})	# number of minutes (saved as 'min')
		(?P<sec>\d{2})	# number of seconds (saved as 'sec')
		\s*				# optional whitespace
		([NSEW])?		# optional directional specifier
		$				# end of string
		""",
		# This pattern attempts to match all other possible specifications of
		#  DMS entry.
		"""
		(-)?			# optional negative sign
		(?P<deg>\d+		# number of degrees (saved as 'deg')
			(\.\d+)?	# optional fractional number of degrees (not saved separately)
		)				# all saved as 'deg'
		\s*				# optional whitespace
		(?:(�|deg))?	# optionally a degrees symbol or the word 'deg' (not saved)
		(?:				# begin optional minutes and seconds
			\s*?			# optional whitespace (matched minimally)
			[, ]?			# optional comma or space (as a delimiter)
			\s*				# optional whitespace
			(?P<min>\d+)	# number of minutes (saved as 'min')
			\s*				# optional whitespace
			(?:('|min))?	# optionally a minutes symbol or the word 'min' (not saved)
			\s*?			# optional whitespace (matched minimally)
			[, ]?			# optional comma or space (as a delimiter)
			\s*				# optional whitespace
			(?P<sec>\d+		# number of seconds
				(?:\.\d+)?	# optional fractional number of seconds (not saved separately)
			)				# (all saved as 'sec')
			\s*				# optional whitespace
			(?:("|sec))?	# optionally a minutes symbol or the word 'min' (not saved)
		)?				# end optional minutes and seconds
		\s*				# optional whitespace
		([NSEW])?		# optional directional specifier
		$				# end of string
		"""
		]
	def __init__( self, DMSString = None ):
		self.SetDMS( DMSString )

	def __float__( self ):
		return self.dd

	def SetDMS( self, DMSString ):
		self.DMSString = string.strip( str( DMSString ) )
		matches = filter( None, map( self._doPattern, self.dmsPatterns ) )
		if len( matches ) == 0:
			raise ValueError, 'String %s did not match any DMS pattern' % self.DMSString
		bestMatch = matches[0]
		self.dd = self._getDDFromMatch( bestMatch )
		del self.DMSString

	def GetDMS( self ):
		deg = int( self.dd )
		fracMin = ( self.dd - deg ) * 60
		min = int( fracMin )
		sec = ( fracMin - min ) * 60
		return ( deg, min, sec )
	DMS = property( GetDMS, SetDMS )
	
	def _doPattern( self, pattern ):
		expression = re.compile( pattern, re.IGNORECASE | re.VERBOSE )
		return expression.match( self.DMSString )
	
	def _getDDFromMatch( self, dmsMatch ):
		# get the negative sign
		isNegative = operator.truth( dmsMatch.group(1) )
		# get SW direction
		isSouthOrWest = operator.truth( dmsMatch.groups()[-1] )
		d = dmsMatch.groupdict()
		# set min & sec to zero if they weren't matched
		if d['min'] is None: d['min'] = 0
		if d['sec'] is None: d['sec'] = 0
		# get the DMS and convert each to float
		d = DictMap( float, d )
		# convert the result to decimal format
		result = d['deg'] + d['min'] / 60 + d['sec'] / 3600
		if isNegative ^ isSouthOrWest: result = -result
		# validate the result
		if not ( 0 <= d['deg'] < 360 and 0 <= d['min'] < 60 and 0 <= d['sec'] < 60 and result >= -180 ):
			raise ValueError, 'DMS not given in valid range (%(deg)f�%(min)f\'%(sec)f").' % d
		return result

# This function takes a Julian day and infers a year by choosing the
#  nearest year to that date.
def GetNearestYearForDay( day ):
	now = time.gmtime()
	result = now.tm_year
	# if the day is far greater than today, it must be from last year
	if day - now.tm_yday > 365/2:
		result -= 1
	# if the day is far less than today, it must be for next year.
	if now.tm_yday - day > 365/2:
		result += 1
	return result

# deprecated with Python 2.3, use datetime.datetime
def ConvertToUTC( t, timeZoneName ):
	t = time.struct_time( t )
	tzi = TimeZoneInformation( timeZoneName )
	if t.tm_isdst in (1,-1):
		raise RuntimeError, 'DST is not currently supported in this function'
	elif t.tm_isdst == 0:
		result = map( operator.add, t, (0,0,0,0,tzi.standardBias,0,0,0,0) )
	else:
		raise ValueError, 'DST flag not in (-1,0-1)'
	result = time.localtime( time.mktime( result ) )
	return result

import os, win32api, win32con, struct, datetime
class Win32TimeZone( datetime.tzinfo ):
	def __init__( self, timeZoneName, fixedStandardTime=False ):
		self.timeZoneName = timeZoneName
		# this key works for WinNT+, but not for the Win95 line.
		tzRegKey = r'SOFTWARE\Microsoft\Windows NT\CurrentVersion\Time Zones'
		tzRegKeyPath = os.path.join( tzRegKey, timeZoneName )
		try:
			key = win32api.RegOpenKeyEx( win32con.HKEY_LOCAL_MACHINE,
										 tzRegKeyPath,
										 0,
										 win32con.KEY_ALL_ACCESS )
		except:
			raise ValueError, 'Timezone Name %s not found.' % timeZoneName
		self.LoadInfoFromKey( key )
		self.fixedStandardTime = fixedStandardTime

	def LoadInfoFromKey( self, key ):
		self.displayName = win32api.RegQueryValueEx( key, "Display" )[0]
		self.standardName = win32api.RegQueryValueEx( key, "Std" )[0]
		self.daylightName = win32api.RegQueryValueEx( key, "Dlt" )[0]
		winTZI, type = win32api.RegQueryValueEx( key, "TZI" )
		winTZI = struct.unpack( '3l8h8h', winTZI )
		makeMinuteTimeDelta = lambda x: datetime.timedelta( minutes = x )
		self.bias, self.standardBiasOffset, self.daylightBiasOffset = \
				   map( makeMinuteTimeDelta, winTZI[:3] )
		self.daylightEnd, self.daylightStart = winTZI[3:11], winTZI[11:19]

	def __repr__( self ):
		return '%s( %s )' % ( self.__class__.__name__, self.timeZoneName )

	def __str__( self ):
		return self.displayName

	def tzname( self, dt ):
		if self.dst( dt ) == self.daylightBiasOffset:
			result = self.daylightName
		elif self.dst( dt ) == self.standardBiasOffset:
			result = self.standardName
		return result
		
	def _getStandardBias( self ):
		return self.bias + self.standardBiasOffset
	standardBias = property( _getStandardBias )

	def _getDaylightBias( self ):
		return self.bias + self.daylightBiasOffset
	daylightBias = property( _getDaylightBias )

	def utcoffset( self, dt ):
		return -( self.bias + self.dst( dt ) )

	def dst( self, dt ):
		assert dt.tzinfo is self
		result = self.standardBiasOffset

		try:
			dstStart = self.GetDSTStartTime( dt.year )
			dstEnd = self.GetDSTEndTime( dt.year )

			if dstStart <= dt.replace( tzinfo=None ) < dstEnd and not self.fixedStandardTime:
				result = self.daylightBiasOffset
		except ValueError:
			# there was probably an error parsing the time zone, which is normal when a
			#  start and end time are not specified.
			pass

		return result

	def GetDSTStartTime( self, year ):
		return self.LocateDay( year, self.daylightStart )

	def GetDSTEndTime( self, year ):
		return self.LocateDay( year, self.daylightEnd )
	
	def LocateDay( self, year, win32SystemTime ):
		month = win32SystemTime[ 1 ]
		# MS stores Sunday as 0, Python datetime stores Monday as zero
		targetWeekday = ( win32SystemTime[ 2 ] + 6 ) % 7
		# win32SystemTime[3] is the week of the month, so the following
		#  is the first possible day
		day = ( win32SystemTime[ 3 ] - 1 ) * 7 + 1
		hour, min, sec, msec = win32SystemTime[4:]
		result = datetime.datetime( year, month, day, hour, min, sec, msec )
		daysToGo = targetWeekday - result.weekday()
		result += datetime.timedelta( daysToGo )
		# if we selected a day in the month following the target month,
		#  move back a week or two.
		while result.month == month + 1:
			result -= datetime.timedelta( weeks = 1 )
		return result

	def _GetTimeZones( ):
		tzRegKey = r'SOFTWARE\Microsoft\Windows NT\CurrentVersion\Time Zones'
		key = win32api.RegOpenKeyEx( win32con.HKEY_LOCAL_MACHINE,
									 tzRegKey,
									 0,
									 win32con.KEY_ALL_ACCESS )
		return RegKeyEnumerator( key )
		
	GetTimeZones = staticmethod( _GetTimeZones )

def GregorianDate( year, julianDay ):
	result = datetime.date( year, 1, 1 )
	result += datetime.timedelta( days = julianDay - 1 )
	return result

def ReplaceList( object, substitutions ):
	try:
		for old, new in substitutions:
			object = object.replace( old, new )
	except AttributeError:
		# object does not have a replace method
		pass
	return object

def ReverseLists( lists ):
	tLists = zip( *lists )
	tLists.reverse()
	return zip( *tLists )

def RegKeyEnumerator( key ):
	index = 0
	try:
		while 1:
			yield win32api.RegEnumKey( key, index )
			index += 1
	except win32api.error: pass

# calculate the seconds for each period
secondsPerMinute = 60
secondsPerHour = 60 * secondsPerMinute
secondsPerDay = 24 * secondsPerHour
secondsPerYear = 365 * secondsPerDay

def getPeriodSeconds( period ):
	"""
	return the number of seconds in the specified period
	"""
	try:
		if isinstance( period, basestring ):
			result = eval( 'secondsPer%s' % string.capwords( period ) )
		elif isinstance( period, ( int, long ) ):
			result = period
		else:
			raise TypeError, 'period must be a string or integer'
	except NameError:
		raise ValueError, "period not in ( minute, hour, day, year )"
	return result

def getDateFormatString( period ):
	"""
	for a given period (e.g. 'month', 'day', or some numeric interval
	such as 3600 (in secs)), return the format string that can be
	used with strftime to format that time to specify the times
	across that interval, but no more detailed.
	so,
	getDateFormatString( 'month' ) == '%Y-%m'
	getDateFormatString( 3600 ) == getDateFormatString( 'hour' ) == '%Y-%m-%d %H'
	getDateFormatString( None ) -> raise TypeError
	getDateFormatString( 'garbage' ) -> raise ValueError
	"""
	# handle the special case of 'month' which doesn't have
	#  a static interval in seconds
	if isinstance( period, basestring ) and string.lower( period ) == 'month':
		result = '%Y-%m'
	else:
		filePeriodSecs = getPeriodSeconds( period )
		formatPieces = ( '%Y', '-%m-%d', ' %H', '-%M', '-%S' )
		intervals = ( secondsPerYear, secondsPerDay, secondsPerHour, secondsPerMinute, 1 )
		mods = map( lambda interval: filePeriodSecs % interval, intervals )
		formatPieces = formatPieces[ : mods.index( 0 ) + 1 ]
		result = string.join( formatPieces, '' )
	return result

import logging, time
class TimestampFileHandler( logging.StreamHandler ):
	"""
	A logging handler which will log to a file, similar to
	logging.handlers.RotatingFileHandler, but instead of
	appending a number, uses a timestamp to periodically select
	new file names to log to.
	"""
	def __init__( self, baseFilename, mode='a', period='day', timeConverter=time.localtime ):
		self.baseFilename = baseFilename
		self.mode = mode
		self._setPeriod( period )
		self.timeConverter = timeConverter
		logging.StreamHandler.__init__( self, None )

	def _setPeriod( self, period ):
		"""
		Set the period for the timestamp.  If period is 0 or None, no period will be used
		"""
		self._period = period
		if period:
			self._periodSeconds = getPeriodSeconds( self._period )
			self._dateFormat = getDateFormatString( self._periodSeconds )
		else:
			self._periodSeconds = 0
			self._dateFormat = ''

	def _getPeriod( self ):
		return self._period
	period = property( _getPeriod, _setPeriod )
	
	def _useFile( self, filename ):
		self._ensureDirectoryExists( filename )
		self.stream = open( filename, self.mode )

	def _ensureDirectoryExists( self, filename ):
		dirname = os.path.dirname( filename )
		if dirname and not os.path.exists( dirname ):
			os.makedirs( dirname )

	def getFilename( self, t ):
		"""
		Return the appropriate filename for the given time
		based on the defined period.
		"""
		root, ext = os.path.splitext( self.baseFilename )
		# remove seconds not significant to the period
		if self._periodSeconds:
			t -= t % self._periodSeconds
		# convert it to a time tuple for formatting using
		#  the supplied converter
		timeTuple = self.timeConverter( t )
		# append the datestring to the filename
		appendedDate = time.strftime( self._dateFormat, timeTuple )
		if appendedDate:
			# in the future, it would be nice for this format
			#  to be supplied as a parameter.
			result = root + ' ' + appendedDate + ext
		else:
			result = self.baseFilename
		return result

	def emit(self, record):
		"""
		Emit a record.

		Output the record to the file, ensuring that the currently-
		opened file has the correct date.
		"""
		now = time.time()
		currentName = self.getFilename( now )
		try:
			if not self.stream.name == currentName:
				self._useFile( currentName )
		except AttributeError:
			# a stream has not been created, so create one.
			self._useFile( currentName )
		logging.StreamHandler.emit(self, record)

	def close( self ):
		"""
		Closes the stream.
		"""
		try:
			self.stream.close()
		except AttributeError: pass

class LogFileWrapper( object ):
	"""
	Emulates a file to replace stdout or stderr or
	anothe file object and redirects its output to
	a logger.
	
	Since data will often be send in partial lines or
	multiple lines, data is queued up until a new line
	is received.  Each line of text is send to the
	logger separately.
	"""
	def __init__(self, name, lvl = logging.DEBUG ):
		self.logger = logging.getLogger( name )
		self.lvl = lvl
		self.queued = ''

	def write(self, data):
		data = self.queued + data
		data = string.split( data, '\n')
		for line in data[:-1]:
			self.logger.log( self.lvl, line )
		self.queued = data[-1]
