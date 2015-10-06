import urllib2
import os
import sys
import json
import time

import settings

requestUrlPattern = 'http://www.reddit.com/%s.json'
jsonFileNamePattern = '%s_page_%d_comments.json'


def processCommentJson(jsonComment, userList):
    # Create a dict from the current comment data.
    if jsonComment['kind'] == 'more':
        return

    commentData = jsonComment['data']
    authorId = commentData['author'].encode('ascii', errors='ignore')
    userList.append(authorId)

    # Recursively process the children comments.
    if 'data' in commentData['replies']:
        jsonCommentList = commentData['replies']['data']['children']
        for childJsonComment in jsonCommentList:
            processCommentJson(childJsonComment, userList)


def parseSubData(subId, page):
    settingsDict = settings.loadSettings()

    jsonFileName = jsonFileNamePattern % (subId, page)
    jsonFilePath = os.path.join(settingsDict['subCommentersJsonDataDir'], jsonFileName)

    try:
        jsonFile = open(jsonFilePath, 'r')
        jsonData = json.load(jsonFile)
    except:
        return None, None

    jsonCommentList = jsonData[1]['data']['children']
    apiAfter = jsonData[1]['data']['after']
    userList = []
    for jsonComment in jsonCommentList:
        processCommentJson(jsonComment, userList)
    
    jsonFile.close()
    return userList, apiAfter

# Returns true if the API call succeeds and false otherwise.
def downloadSubCommenters(subId, commentsPerRequest, apiAfter, apiCount, page):
    settingsDict = settings.loadSettings()

    redditUrl = requestUrlPattern % subId    
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

    jsonFileName = jsonFileNamePattern % (subId, page)
    filePath = os.path.join(settingsDict['subCommentersJsonDataDir'], jsonFileName)
    localJsonFile = open(filePath, 'w')
    localJsonFile.write(jsonData)
    localJsonFile.close()

    # Sleep to prevent hitting Reddit API rate limit.
    time.sleep(2)
    return True 

def get_sub_commenters(subId):
    createDataDirs()

    settingsDict = settings.loadSettings()
    print 'Downloading comment data for submission %s.' % subId

    # Make the first request.
    numberOfRequests = 100
    apiAfter = None
    apiCount = 0
    page = 1
    
    commentsPerRequest = int(settingsDict['http']['commentsPerRequest'])
    if downloadSubCommenters(subId, commentsPerRequest, apiAfter, apiCount, page):
        userList, apiAfter = parseSubData(subId, page)
        if userList is None:
            return None

        apiCount += len(userList)
        page += 1
    else:
        return None

    # Download the remaining pages.
    maxRequests =  int(settingsDict['http']['maxRequests'])
    while (page - 1) <= maxRequests and apiAfter != None:
        if downloadSubCommenters(subId, commentsPerRequest, apiAfter, apiCount, page):
            partialUserList, apiAfter = parseSubData(subId, page)
            if partialUserList is None:
                break

            userList = userList + partialUserList
            apiCount += len(userList)
            page += 1
        else:
            break

    return list(set(userList))

def downloadSubData(subId):
    userList = get_sub_commenters(subId)
    if userList is not None:
        userListFile = open('%s.csv' % subId, 'w')

        for user in userList:
            userListFile.write(user + '\n')

        userListFile.close()


def createDataDirs():
    '''
    Create directories to save data if they do not exist.
    '''
    settingsDict = settings.loadSettings()

    if not os.path.exists(settingsDict['subCommentersCsvDataDir']):
        os.makedirs(settingsDict['subCommentersCsvDataDir'])

    if not os.path.exists(settingsDict['subCommentersJsonDataDir']):
        os.makedirs(settingsDict['subCommentersJsonDataDir'])


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print 'Usage:'
        print 'python get_sub_commenters.py [submission_id]'
        sys.exit()
    subId = sys.argv[1]
    downloadSubData(subId)

