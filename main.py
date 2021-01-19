import json
import os
import logging
import re

debug = True


def loggingConfig():
    if debug:
        logging.basicConfig(
            format='%(asctime)s - %(filename)s - %(levelname)s : %(message)s',
            level=logging.DEBUG,
            datefmt='%Y-%m-%d %H:%M:%S'
        )
    else:
        logging.basicConfig(
            filename='main.log',
            format='%(asctime)s - %(filename)s - %(levelname)s : %(message)s',
            level=logging.INFO,
            filemode='a',
            datefmt='%Y-%m-%d %H:%M:%S'
        )


def readConfig():
    """"读取配置"""
    with open("config.json") as json_file:
        config = json.load(json_file)
    return config


def fileLists(root, fileType, escapeFolder, loop):
    """查找文件"""
    '''
    String root 文件夹路径
    List fileType 文件后缀
    List escapeFolder 排除的文件夹名
    Int loop 最大搜索深度
    
    List total 满足条件的所有文件路径
    '''
    for folder in escapeFolder:
        if folder in root:
            return []
    total = []
    dirs = os.listdir(root)
    for entry in dirs:
        f = os.path.join(root, entry)
        if os.path.isdir(f) and loop > 0:
            total += fileLists(f, fileType, escapeFolder, loop - 1)
        elif os.path.splitext(f)[1] in fileType:
            total.append(f)
            logging.info('[-] ' + os.path.basename(f))
    return total


def animeLists(root, escapeFolder, loop):
    """查找动画文件"""
    fileType = ['.mp4', '.avi', '.rmvb', '.wmv', '.mov', '.mkv', '.flv', '.ts', '.webm', '.MP4', '.AVI', '.RMVB',
                '.WMV', '.MOV', '.MKV', '.FLV', '.TS', '.WEBM', '.iso', '.ISO']
    logging.info('[*] Start find anime file(s)')
    return fileLists(root, fileType, escapeFolder, loop)


def subtitleLists(root, escapeFolder, loop):
    """查找字幕文件"""
    fileType = ['.srt', '.ass', '.SRT', '.ASS']
    logging.info('[*] Start find subtitles file(s)')
    return fileLists(root, fileType, escapeFolder, loop)


def findAnimeName(folderName):
    """通过文件夹名识别动漫名"""
    '''
    String folderName 文件夹名
    去除所有括号内的内容
    String animeName 动漫名
    '''
    rawAnimeName = re.sub(u"\\(.*?\\)|\\{.*?\\}|\\[.*?\\]|\\<.*?\\>", "", folderName)
    animeName = rawAnimeName.strip()
    logging.debug('[!] AnimeName: ' + animeName + ' <- ' + folderName)
    return animeName


def findEpisode(fileName, animeName):
    """通过文件名和动漫名识别第几集"""
    '''
    String fileName 文件名
    String animeName 动漫名
    从文件名中删去动漫名，去掉所有括号内的内容，只保留数字;
    或者从文件名中删去动漫名，匹配[xxx]形式，提取数字xxx
    Int/None episode 集数
    '''
    fileName = os.path.basename(fileName)
    fileName = os.path.splitext(fileName)[0]
    try:
        rawEpisode = re.sub(animeName, '', fileName)
        delBraceRawEpisode = re.sub(u"\\(.*?\\)|\\{.*?\\}|\\[.*?\\]|\\<.*?\\>", "", rawEpisode)
        delBraceRawEpisode = delBraceRawEpisode.strip()
        if len(delBraceRawEpisode) == 0:
            episode = re.findall('\[(\d+)\]', rawEpisode)[0]
        else:
            episode = re.findall('\d+', delBraceRawEpisode)[0]
        logging.debug('[!] EpisodeName: ' + animeName + ' ' + episode + ' <- ' + fileName)
        return episode
    except Exception as e:
        logging.debug('[!] EpisodeNameException: ' + fileName)
        return


def createLink(sourcePath, targetPath):
    """创建硬链接"""
    '''
    当DEBUG模式时只输出日志，不真的创建连接
    '''
    sourcePath = os.path.abspath(sourcePath)
    targetPath = os.path.abspath(targetPath)
    if not os.path.exists(targetPath):
        if os.path.exists(os.path.join(os.path.dirname(targetPath), 'link.ignore')):
            logging.debug('[-] IgnoreLink: ' + targetPath + ' <- ' + sourcePath)
        elif debug:
            logging.debug('[-] FakeLink: ' + targetPath + ' <- ' + sourcePath)
        else:
            if not os.path.exists(os.path.dirname(targetPath)):
                os.makedirs(os.path.dirname(targetPath))
            os.link(sourcePath, targetPath)
            logging.info('[+] Link:' + targetPath + ' <- ' + sourcePath)


def getDirName(path):
    """获取文件夹名"""
    path = os.path.abspath(path)
    name = os.path.basename(os.path.dirname(path))
    logging.debug('[-] DirName: ' + name + ' <- ' + path)
    return name


def targetPath(sourcePath, baseSourcePath, baseTargetPath):
    """获取准备创建硬链接的路径"""
    relPath = os.path.relpath(sourcePath, baseSourcePath)
    animeName = findAnimeName(getDirName(relPath))
    episode = findEpisode(relPath, animeName)
    if episode is None:
        return
    downPath = os.path.dirname(os.path.dirname(relPath))
    target = os.path.join(os.path.join(downPath, animeName), episode + os.path.splitext(sourcePath)[1])
    logging.debug('[-] TargetPath: ' + os.path.join(baseTargetPath, target) + ' <- ' + sourcePath)
    return os.path.join(baseTargetPath, target)


def main():
    config = readConfig()
    sourceDir = config['sourceDir']
    targetDir = config['targetDir']
    global debug
    debug = bool(config['debug'])
    loggingConfig()
    if debug:
        logging.info('[!] ======== DEBUG MODE ========')
    logging.info('[*] Running: ' + sourceDir + ' -> ' + targetDir)
    os.chdir(sourceDir)
    animeList = animeLists(sourceDir, [], 1)
    logging.info('[*] Start link anime file(s)')
    for animePath in animeList:
        animeTarget = targetPath(animePath, sourceDir, targetDir)
        createLink(animePath, animeTarget)
    logging.info('[*] End link anime file(s)')
    subtitleListSource = subtitleLists(sourceDir, [], 1)
    logging.info('[*] Start link source subtitle file(s)')
    for subtitlePath in subtitleListSource:
        subtitleTarget = targetPath(subtitlePath, sourceDir, targetDir)
        createLink(subtitlePath, subtitleTarget)
    logging.info('[*] End link source subtitle file(s)')
    subtitleListTarget = subtitleLists(targetDir, [], 1)
    logging.info('[*] Start link target subtitle file(s)')
    for subtitlePath in subtitleListTarget:
        subtitleTarget = targetPath(subtitlePath, targetDir, targetDir)
        createLink(subtitlePath, subtitleTarget)
    logging.info('[*] End link target subtitle file(s)')


if __name__ == '__main__':
    main()
