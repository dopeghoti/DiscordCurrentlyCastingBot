import os, sqlite3
from dotenv import load_dotenv

class Database( object ):
    """Wrapper for SQLite3 Database for use in the Now Playing Bot"""

    def __init__( self, db_location = None ):
        """Initialize the class variables, create the schema in the DB if not already preasent"""
        if db_location is None:
            load_dotenv()
            db_location = os.getenv( 'CHANNELS' )
        if db_location is not None:
            try:
                self.__connection = sqlite3.connect( db_location )
                self.cursor = self.__connection.cursor()
            except sqlite3.Error as e:
                print( 'Error connecing to database!' )
                print( f'{e}' )
        else:
            raise 'BadDatabaseInit'
        # Make sure our table is actually there
        self.query( 'CREATE TABLE IF NOT EXISTS channels ( id INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL, channel VARCHAR(127) )' )

    def __del__ ( self ):
        self.close()

    def __enter__( self ):
        return self

    def __exit__( self, ext_Type, exc_value, traceback ):
        self.cursor.close()
        if isinstance( exc_value, Exception ):
            self.__connection.rollback()
        else:
            self.__connection.commit()
        self.__connection.close()

    def close( self ):
        """CLose the SQLite3 connection"""
        if self.__connection:
            self.__connection.commit()
            self.cursor.close()
            self.__connection.close()

    def query( self, sql ):
        """Execute the provised SQL query.  If SELECTing, you can get results from the cursor."""
        self.cursor.execute( sql )

    def getStreamerList( self ):
        """Fetches the list of active channels, returns a List of them."""
        self.query( 'SELECT channel FROM channels ORDER BY Channel ASC' )
        rawdata =  self.cursor.fetchall()
        streamerlist = []
        for streamer in rawdata:
            streamerlist.append( streamer[0] )
        return streamerlist

    def checkStreamerList( self, channel = None ):
        """Returns True if the provided channel is on the List; False otherwise."""
        if channel.lower() in self.getStreamerList():
            return True
        else:
            return False

    def addToList( self, channel = None ):
        """Adds the specified streamer to the list, or returns False if it is already there
        (or if no channel is specified)."""
        if channel:
            if self.checkStreamerList( channel ):
                return False
            else:
                self.query( f"INSERT INTO channels (channel) VALUES ('{channel.lower()}' )" )
                return True
        else:
            return False

    def removeFromList( self, channel = None ):
        """Removes the specified streamer from the list, or returns False if it is not there
        (or if no channel is specified)."""
        if channel:
            if self.checkStreamerList( channel ):
                self.query( f"DELETE FROM channels WHERE LOWER( channel ) = '{channel.lower()}'" )
                return True
            else:
                return False
        else:
            return False


