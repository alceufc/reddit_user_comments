import urllib2
import os
import sys
import json
import time

import settings

requestUrlPattern = 'http://www.reddit.com/user/%s/comments.json'
jsonFileNamePattern = '%s_page_%d_comments.json'

def generateCsvUserData(commentDictList, userId):
    settingsDict = settings.loadSettings()

    # Save on a Matlab readable format.
    filePath = os.path.join(settingsDict['userCommentsCsvDataDir'], '%s_comments.csv' % userId)
    dataFile = open(filePath, 'w')
    for d in commentDictList:
        dataFile.write('%d, %d, %d, %d\n' %  (
            d['creation_time'], 
            d['upvotes'], 
            d['downvotes'],
            len(d['text']) ))
    dataFile.close()

    # Save a second file with the comments ids.
    filePath = os.path.join(settingsDict['userCommentsCsvDataDir'], '%s_com_ids.csv' % userId)
    dataFile = open(filePath, 'w')
    for d in commentDictList:
        dataFile.write('%s\n' %  (d['comment_id']))
    dataFile.close()


def parseUserCommentData(userId, page):
    settingsDict = settings.loadSettings()

    jsonFileName = jsonFileNamePattern % (userId, page)
    jsonFilePath = os.path.join(settingsDict['userCommentsJsonDataDir'], jsonFileName)

    try:
        jsonFile = open(jsonFilePath, 'r')
        jsonData = json.load(jsonFile)
    except:
        return None, None

    jsonCommentList = jsonData['data']['children']
    apiAfter = jsonData['data']['after']
    commentDictList = []
    for jsonComment in jsonCommentList:
        commentDict = {}

        commentData = jsonComment['data']
        commentDict['comment_id'] = commentData['id'].encode('ascii', errors='ignore')
        commentDict['upvotes'] = int(commentData['ups'])
        commentDict['downvotes'] = int(commentData['downs'])
        commentDict['creation_time'] = int(commentData['created_utc'])
        commentDict['subreddit'] = commentData['subreddit'].encode('ascii', errors='ignore')
        commentDict['user_id'] = commentData['author'].encode('ascii', errors='ignore')
        commentDict['text'] = commentData['body'].encode('ascii', errors='ignore').translate(None, '\r\n\t"')

        parent_id = commentData['parent_id'].encode('ascii', errors='ignore')
        parent_id = parent_id.split('_')[1]
        commentDict['parent_id'] = parent_id

        submission_id = commentData['link_id'].encode('ascii', errors='ignore')
        submission_id = submission_id.split('_')[1]
        commentDict['submission_id'] = submission_id

        commentDictList.append(commentDict)
    
    jsonFile.close()
    return commentDictList, apiAfter

# Returns true if the API call succeeds and false otherwise.
def downloadUserComments(userId, commentsPerRequest, apiAfter, apiCount, page):
    settingsDict = settings.loadSettings()

    redditUrl = requestUrlPattern % userId    
    redditUrl += '?limit=%d' % commentsPerRequest
    if apiAfter != None:
        redditUrl += '&after=%s' % apiAfter
    if apiCount > 0:
        redditUrl += '&count=%d' % apiCount

    print redditUrl
    headerDict = { 'User-Agent': settingsDict['http']['userAgent']}
    req = urllib2.Request(redditUrl, None, headerDict)

    # Make the HTTP request
    try:
        httpResponse = urllib2.urlopen(req)
        jsonData = httpResponse.read()
    except urllib2.HTTPError as e:
        # If the request fails, ignore it.
        print(e.reason)
        return
    except:
        print 'Unknown error.'
        return False

    jsonFileName = jsonFileNamePattern % (userId, page)
    filePath = os.path.join(settingsDict['userCommentsJsonDataDir'], jsonFileName)
    localJsonFile = open(filePath, 'w')
    localJsonFile.write(jsonData)
    localJsonFile.close()

    # Sleep to prevent hitting Reddit API rate limit.
    time.sleep(2)
    return True 

def get_user_comments(userId):
    settingsDict = settings.loadSettings()
    print 'Downloading comment data for user %s.' % userId

    # Make the first request.
    numberOfRequests = 100
    apiAfter = None
    apiCount = 0
    page = 1
    
    commentsPerRequest = int(settingsDict['http']['commentsPerRequest'])
    if downloadUserComments(userId, commentsPerRequest, apiAfter, apiCount, page):
        commentDictList, apiAfter = parseUserCommentData(userId, page)
        if commentDictList is None:
            return None

        apiCount += len(commentDictList)
        page += 1
    else:
        return None

    # Download the remaining pages.
    maxRequests =  int(settingsDict['http']['maxRequests'])
    while (page - 1) <= maxRequests and apiAfter != None:
        if downloadUserComments(userId, commentsPerRequest, apiAfter, apiCount, page):
            partialCommentList, apiAfter = parseUserCommentData(userId, page)
            if partialCommentList is None:
                break

            commentDictList.extend(partialCommentList)
            apiCount += len(partialCommentList)
            page += 1
        else:
            break

    return commentDictList

def downloadUserData(userId):
    commentDictList = get_user_comments(userId)
    if commentDictList is not None:
        generateCsvUserData(commentDictList, userId)

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print 'Usage:'
        print 'python get_user_comments.py [reddit_user_id]'
        sys.exit()
    userId = sys.argv[1]
    downloadUserData(userId)

