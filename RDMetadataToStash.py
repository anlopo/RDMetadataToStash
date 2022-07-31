#!/usr/bin/python3

import sqlite3
import configparser
import hashlib
import datetime
import argparse
import os

# Instantiate the arg parser
parser = argparse.ArgumentParser(description='RedditDownloader Metadata to Stash Database Python Script')

parser.add_argument('--config', '-C', type=str, help='path to config file')
parser.add_argument('--rddb', '-o', type=str, help='path to RedditDownloader Metadata DB')
parser.add_argument('--rddir', '-d', type=str, help='path to RedditDownloader download directory')
parser.add_argument('--stashdb', '-s', type=str, help='path to Stash DB')
parser.add_argument('--missing', '-l', type=str, help='file to store missing log')
parser.add_argument('--quiet', action='store_true', help='Be quiet')

args = parser.parse_args()

if args.quiet == False:
  print("=== Script START ===")

config = configparser.ConfigParser()
if args.config != None:
  if config.read(args.config) == None:
    print("Config file read error!")
    exit()
else:
  if config.read('RDMetadataToStash.ini') == None:
    print("Config file read error!")
    exit()

if args.rddb != None:
  RDDBfilepath = args.rddb
else:
  RDDBfilepath = config['RDDB']['filepath']

if args.rddir != None:
  RDdir = args.rddir
else:
  RDdir = config['RDDB']['pathtodir']

if args.quiet == False:
  print("RDDB filepath: " + RDDBfilepath)

if args.stashdb != None:
  StashDBfilepath = args.stashdb
else:
  StashDBfilepath = config['StashDB']['filepath']

if args.quiet == False:
  print("StashDB filepath: " + StashDBfilepath)

# Most of missing files are duplicates, Stash don't add files with same hash to its DB
if args.missing != None:
  missingLogFilePath = args.missing
else:
  missingLogFilePath = config['LOG']['missing_logfile']
missingLogFile = open(missingLogFilePath, "a", encoding="utf-8")
missingLogFile.write("\n\n=== RUN FROM " + str(datetime.datetime.now()) + " - " + RDDBfilepath + " - " + StashDBfilepath + " ===\n")

localTimeZone = config['SETTINGS']['localTimeZone']
localTimeZoneSeconds = config['SETTINGS']['localTimeZoneSeconds']

StashDB = sqlite3.connect(StashDBfilepath)
RDDB = sqlite3.connect(RDDBfilepath)

StashDBcur = StashDB.cursor()
RDDBcur = RDDB.cursor()
RDDBcur2 = RDDB.cursor()

# Read Reddit studio ID, create if not found
StashDBcur.execute("SELECT id FROM studios WHERE name LIKE 'Reddit%'")
RDstudioID = StashDBcur.fetchone()
if RDstudioID != None:
  if args.quiet == False:
    print("Studio ID for Reddit is " + str(RDstudioID[0]))
else:
  if args.quiet == False:
    print("Studio with name Reddit does not exist, creating.")
  toHash = "Reddit"
  hashedName = hashlib.md5(toHash.encode())
  dt = datetime.datetime.now()
  StashDBcur.execute("INSERT INTO studios (name, url, checksum, created_at, updated_at) VALUES ('Reddit','https://www.reddit.com','" + hashedName.hexdigest() + "', '" + str(dt) + "', '" + str(dt) + "')")
  StashDB.commit()
  StashDBcur.execute("SELECT id FROM studios WHERE name LIKE 'Reddit%'")
  RDstudioID = StashDBcur.fetchone()
  if args.quiet == False:
    print("Created Studio Reddit and ist ID is " + str(RDstudioID[0]))

missingMediasNum = 0
alredyUpdatedNum = 0
updatedNum = 0
rowsParsed = 0

# Get medias ID
for row in RDDBcur.execute("SELECT files.path, urls.post_id FROM files INNER JOIN urls ON files.id = urls.file_id WHERE downloaded = '1' ORDER BY files.id"):
  rowsParsed = rowsParsed + 1
  filePath = RDdir + os.path.sep + row[0]
  #filePath = RDdir + "/" + row[0]

  # Get media type
  if ".gif" in row[0] or ".jpg" in row[0] or ".png" in row[0] or ".svg" in row[0]:
    ftype = "Image"
  elif ".mp4" in row[0] or ".webm" in row[0] or ".m4a" in row[0]:
    ftype = "Video"
  else:
    print(filePath)

  # If mediatype is Image
  if ftype == "Image":
    # Get ID for medias path
    StashDBcur.execute("SELECT id, title FROM images WHERE path = ?", (str(filePath),))
    mediaID = StashDBcur.fetchone()
    if mediaID != None:
      # Get media Details from corensponding table
      RDDBcur2.execute("SELECT author, type, title, subreddit, created_utc FROM posts WHERE reddit_id = '" + str(row[1]) + "'")
      details = RDDBcur2.fetchone()

      creationdatefromRDTitle = datetime.datetime.utcfromtimestamp(details[4]+int(localTimeZoneSeconds)).strftime('%Y-%m-%d %H:%M:%S')

      # Check if media is alredy updated by this script by checking title for date in right format
      if str(creationdatefromRDTitle) in mediaID[1]:
        alredyUpdatedNum = alredyUpdatedNum + 1
      else:
        updatedNum = updatedNum + 1

        # Generate title
        title = details[3] + " - " + details[0] + " - " + details[2] + " - " + str(creationdatefromRDTitle)
        creationdatefromRD = datetime.datetime.utcfromtimestamp(details[4]+int(localTimeZoneSeconds)).strftime("%Y-%m-%dT%H:%M:%S") + localTimeZone # 2021-02-26T20:47:53+01:00
        modTime = datetime.datetime.now().strftime("%Y-%m-%dT%H:%M:%S") + localTimeZone # 2021-02-26T20:47:53+01:00

        # Update title, Studio ID, Post date, modification date (actual timedate)
        # print("UPDATE images SET title='" + title + "', studio_id='" + str(RDstudioID[0]) + "', created_at='" + str(creationdatefromRD) +\
        #   "', updated_at='" + modTime + "' WHERE id = '" + str(mediaID[0]) + "'")
        StashDBcur.execute("UPDATE images SET title=?, studio_id=?, created_at=?, updated_at=? WHERE id = ?", (title, str(RDstudioID[0]), \
          str(creationdatefromRD), modTime, str(mediaID[0])))
    else:
      # If filepath is not found in StashDB add it to missing log file
      missingLogFile.write("Image - " + filePath + "\n")
      missingMediasNum = missingMediasNum + 1
  # If mediatype is Video
  elif ftype == "Video":
    # Get ID for medias path
    StashDBcur.execute("SELECT id, title FROM scenes WHERE path = ?", (str(filePath),))
    mediaID = StashDBcur.fetchone()
    if mediaID != None:
      # Get media Details from corensponding table
      RDDBcur2.execute("SELECT author, type, title, body, subreddit, over_18, created_utc, num_comments, score FROM posts WHERE reddit_id = '" + str(row[1]) + "'")
      details = RDDBcur2.fetchone()

      creationdatefromRDTitle = datetime.datetime.utcfromtimestamp(details[6]+int(localTimeZoneSeconds)).strftime('%Y-%m-%d %H:%M:%S')

      # Check if media is alredy updated by this script by checking title for date in right format
      if str(creationdatefromRDTitle) in mediaID[1]:
        alredyUpdatedNum = alredyUpdatedNum + 1
      else:
        updatedNum = updatedNum + 1
        
        # Generate title
        title = details[4] + " - " + details[0] + " - " + details[2] + " - " + str(creationdatefromRDTitle)
        creationdatefromRDDate = datetime.datetime.utcfromtimestamp(details[6]+int(localTimeZoneSeconds)).strftime('%Y-%m-%d %H:%M:%S.%f')
        creationdatefromRD = datetime.datetime.utcfromtimestamp(details[6]+int(localTimeZoneSeconds)).strftime("%Y-%m-%dT%H:%M:%S") + localTimeZone # 2021-02-26T20:47:53+01:00
        modTime = datetime.datetime.now().strftime("%Y-%m-%dT%H:%M:%S") + localTimeZone # 2021-02-26T20:47:53+01:00
        
        # Generate details
        sceneDetails = "Subreddit: " + str(details[4]) + "\nAutor: " + str(details[0]) + "\nType: " + details[1] + "\n\n" + details[2] + "\n" + details[3] +\
           "\n\nComments: " + str(details[7]) + "\nScore: " + str(details[8]) + " over18: " + str(bool(details[2]))

        # Generate link to RD Post
        linkToPost = "https://www.reddit.com/comments/" + str(row[1].replace('t3_', ''))

        # Update title, Studio ID, Post date, modification date (actual timedate), link to OF Post and Details
        # print("UPDATE scenes SET title=" + title + ", details=" + sceneDetails + ", url=" + linkToPost + ", date=" + creationdatefromRDDate +\
        #   ", studio_id=" + str(RDstudioID[0]) + ", created_at=" + creationdatefromRD + ", updated_at=" + modTime + " WHERE id = " + str(mediaID[0]))
        StashDBcur.execute("UPDATE scenes SET title=?, details=?, url=?, date=?, studio_id=?, created_at=?, updated_at=? WHERE id = ?", (title, sceneDetails, linkToPost, \
          creationdatefromRDDate, RDstudioID[0], str(creationdatefromRD), modTime, mediaID[0]))
    # If filepath is not found in StashDB add it to missing log file
    else:
      missingLogFile.write("Video - " + filePath + "\n")
      missingMediasNum = missingMediasNum + 1

# Commit changes to StashDB
StashDB.commit()

missingLogFile.write("Number of records: " + str(rowsParsed) + "\n")
if args.quiet == False:
  print("Number of records: " + str(rowsParsed))
missingLogFile.write("Number of alredy Updated records: " + str(alredyUpdatedNum) + "\n")
if args.quiet == False:
  print("Number of alredy Updated records: " + str(alredyUpdatedNum))
missingLogFile.write("Number of Updated records: " + str(updatedNum) + "\n")
if args.quiet == False:
  print("Number of Updated records: " + str(updatedNum))
elif (updatedNum > 0):
  print("Updated " + str(updatedNum) + " records.")
missingLogFile.write("Number of missing medias: " + str(missingMediasNum) + "\n")
if args.quiet == False:
  print("Number of missing medias: " + str(missingMediasNum))
missingLogFile.write("=== Script DONE ===\n")
if args.quiet == False:
  print("=== Script DONE ===")

# Flush missing media log
missingLogFile.flush()

# Close databases and file
StashDB.close()
RDDB.close()
missingLogFile.close()
