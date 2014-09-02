import time
import os

import get_user_comments
import settings


def getUserNameList():
    '''
    Get a list of users to download comment.
    Do not return users whose data was already processed.
    '''
    settingsDict = settings.loadSettings()

    # Get a list of all users that we want to collect comment data.
    allUsersSet = set()
    userListFile = open(settingsDict['userListFile'], 'r')
    for line in userListFile:
        userName = line.strip()
        if len(userName) > 1:
            allUsersSet.add(userName)
    userListFile.close()

    # Get a list of users that we have already processed.
    downloadedUsersSubset = set()
    for fileName in os.listdir(settingsDict['userCommentsCsvDataDir']):
        subId = os.path.split(fileName)[1].split('_')[0]
        downloadedUsersSubset.add(subId)

    print '%d users in dataset.' % len(allUsersSet)
    print 'Downloaded comments from %d users.' % len(downloadedUsersSubset)
    print '%d users remaining.' % (len(allUsersSet) - len(downloadedUsersSubset))

    # Return the difference.
    return allUsersSet.difference(downloadedUsersSubset)


if __name__ == "__main__":
    userNameSet = getUserNameList()
    for userName in userNameSet:
        get_user_comments.downloadUserData(userName)
